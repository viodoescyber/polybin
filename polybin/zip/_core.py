import io
import zipfile
from pathlib import Path

EOCD_SIG            = 0x06054B50
CD_FILE_SIG         = 0x02014B50
ZIP64_EOCD_SIG      = 0x06064B50
ZIP64_EOCD_LOC_SIG  = 0x07064B50
ZIP64_EXTRA_ID      = 0x0001

def merge_zip_archives_to_bytes(zip_paths):
    """
    Merge multiple ZIP-like archives into one in-memory ZIP.
    Repackages entries; last wins on conflicts.
    """
    store = {}
    for p in (zip_paths or []):
        data = Path(p).read_bytes()
        with zipfile.ZipFile(io.BytesIO(data), "r") as zin:
            for name in zin.namelist():
                store[name] = zin.read(name)

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name, payload in store.items():
            zout.writestr(name, payload)
    return out.getvalue()

def _find_eocd_offset(blob: bytes):
    max_scan = min(len(blob), 66_000)
    tail = blob[-max_scan:]
    sig = b"PK\x05\x06"
    idx = tail.rfind(sig)
    if idx < 0:
        return None
    return len(blob) - max_scan + idx

def patch_zip_for_prepend(zip_bytes: bytes, delta: int) -> bytes:
    """
    Patch central-directory relative offsets so the ZIP can be placed at 'delta'
    inside a larger file (SFX behavior). Also patches Zip64 EOCD and locator if present.
    """
    buf = bytearray(zip_bytes)
    eocd_off = _find_eocd_offset(buf)
    if eocd_off is None:
        raise RuntimeError("EOCD not found; invalid ZIP-like archive.")

    # EOCD fields
    cd_offset = int.from_bytes(buf[eocd_off+16:eocd_off+20], "little")

    # Zip64 locator just before EOCD?
    loc_guess = eocd_off - 20
    has_zip64 = False
    if loc_guess >= 0 and int.from_bytes(buf[loc_guess:loc_guess+4], "little") == ZIP64_EOCD_LOC_SIG:
        has_zip64 = True
        old = int.from_bytes(buf[loc_guess+8:loc_guess+16], "little")
        buf[loc_guess+8:loc_guess+16] = (old + delta).to_bytes(8, "little")

    # Patch Zip64 EOCD CD offset if present
    if has_zip64:
        zip64_eocd_off = int.from_bytes(buf[loc_guess+8:loc_guess+16], "little")
        if 0 <= zip64_eocd_off + 56 <= len(buf):
            old_cd64 = int.from_bytes(buf[zip64_eocd_off+48:zip64_eocd_off+56], "little")
            buf[zip64_eocd_off+48:zip64_eocd_off+56] = (old_cd64 + delta).to_bytes(8, "little")

    # Patch EOCD CD offset (32-bit)
    buf[eocd_off+16:eocd_off+20] = (cd_offset + delta).to_bytes(4, "little")

    # Walk central directory entries and patch 'relative offset of local header'
    pos = cd_offset
    end_cd = eocd_off
    while pos + 46 <= end_cd:
        if int.from_bytes(buf[pos:pos+4], "little") != CD_FILE_SIG:
            break
        fname_len = int.from_bytes(buf[pos+28:pos+30], "little")
        extra_len = int.from_bytes(buf[pos+30:pos+32], "little")
        cmt_len = int.from_bytes(buf[pos+32:pos+34], "little")
        rel_off = int.from_bytes(buf[pos+42:pos+46], "little")

        if rel_off != 0xFFFFFFFF:
            buf[pos+42:pos+46] = (rel_off + delta).to_bytes(4, "little")
        else:
            # try Zip64 extra
            extra_off = pos + 46 + fname_len
            end_extra = extra_off + extra_len
            p = extra_off
            while p + 4 <= end_extra:
                header_id = int.from_bytes(buf[p:p+2], "little")
                data_len = int.from_bytes(buf[p+2:p+4], "little")
                data_start = p + 4
                data_end = data_start + data_len
                if data_end > end_extra:
                    break
                if header_id == ZIP64_EXTRA_ID and data_len >= 8:
                    q = data_start
                    while q + 8 <= data_end:
                        val = int.from_bytes(buf[q:q+8], "little")
                        buf[q:q+8] = (val + delta).to_bytes(8, "little")
                        q += 8
                    break
                p = data_end

        pos = pos + 46 + fname_len + extra_len + cmt_len

    return bytes(buf)
