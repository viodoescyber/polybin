import struct
from typing import Tuple
from ..ico._core import build_overlay_ico_head_256

def be_u32(b: bytes, off: int) -> int:
    return struct.unpack(">I", b[off:off+4])[0]
def be_u64(b: bytes, off: int) -> int:
    return struct.unpack(">Q", b[off:off+8])[0]
def set_be_u32(buf: bytearray, off: int, v: int) -> None:
    buf[off:off+4] = struct.pack(">I", v)
def set_be_u64(buf: bytearray, off: int, v: int) -> None:
    buf[off:off+8] = struct.pack(">Q", v)

def read_box(buf: bytes, off: int):
    if off + 8 > len(buf):
        return None
    size = be_u32(buf, off)
    typ = buf[off+4:off+8]
    hdr = 8
    if size == 1:
        if off + 16 > len(buf):
            return None
        size = be_u64(buf, off+8)
        hdr = 16
    elif size == 0:
        size = len(buf) - off
    if size < hdr or off + size > len(buf):
        return None
    return size, typ, hdr

def iterate_children(buf: bytes, parent_off: int):
    top = read_box(buf, parent_off)
    if not top:
        return
    total, _, hdr = top
    pos = parent_off + hdr
    end = parent_off + total
    while pos + 8 <= end:
        child = read_box(buf, pos)
        if not child:
            break
        sz, typ, chdr = child
        if pos + sz > end:
            break
        yield pos, sz, typ, chdr
        pos += sz

CONTAINERS = {b"moov", b"trak", b"mdia", b"minf", b"stbl"}
def locate_top(buf: bytes, fourcc: bytes):
    pos = 0
    while True:
        box = read_box(buf, pos)
        if not box:
            return None, None, None
        sz, typ, hdr = box
        if typ == fourcc:
            return pos, sz, hdr
        pos += sz

def adjust_stco_co64(buf: bytearray, container_off: int, delta: int):
    for off, sz, typ, hdr in iterate_children(buf, container_off):
        if bytes(typ) in CONTAINERS:
            adjust_stco_co64(buf, off, delta)
        elif typ == b"stco":
            base = off + hdr
            if base + 8 > len(buf): continue
            count = be_u32(buf, base + 4)
            table = base + 8
            for i in range(count):
                eo = table + i*4
                if eo + 4 > len(buf): break
                set_be_u32(buf, eo, be_u32(buf, eo) + delta)
        elif typ == b"co64":
            base = off + hdr
            if base + 8 > len(buf): continue
            count = be_u32(buf, base + 4)
            table = base + 8
            for i in range(count):
                eo = table + i*8
                if eo + 8 > len(buf): break
                set_be_u64(buf, eo, be_u64(buf, eo) + delta)

def _build_ftyp_32() -> bytes:
    b = bytearray(32)
    b[0:4] = struct.pack(">I", 32)
    b[4:8] = b"ftyp"
    b[8:12] = b"isom"
    b[12:16] = struct.pack(">I", 0x200)
    b[16:20] = b"isom"
    b[20:24] = b"iso2"
    b[24:28] = b"avc1"
    b[28:32] = b"mp41"
    return bytes(b)

def rehead_mp4_with_overlay_and_ftyp(
    mp4_bytes: bytes,
    png_size: int,
    png_dim: Tuple[int, int],
    png_offset_abs: int,
) -> bytes:
    """
    Replace the first top-level box of the MP4 with:
      [256-byte ICO overlay] + [32-byte 'ftyp'] + [original remainder]
    Then fix stco/co64 by delta = (256+32 - orig_first_size).
    """
    fb = read_box(mp4_bytes, 0)
    if not fb:
        raise RuntimeError("Invalid MP4: no top-level box at offset 0")
    orig_first_size, orig_first_type, orig_hdr = fb
    if orig_first_size <= 0:
        raise RuntimeError("Invalid MP4: first box size is zero/negative")

    remainder = mp4_bytes[orig_first_size:]

    overlay = build_overlay_ico_head_256(
        png_size=png_size,
        png_offset_abs=png_offset_abs,
        width_px=png_dim[0],
        height_px=png_dim[1],
    )
    ftyp = _build_ftyp_32()

    new_mp4 = bytearray(overlay + ftyp + remainder)
    delta = (256 + 32) - orig_first_size

    moov_off, moov_size, moov_hdr = locate_top(new_mp4, b"moov")
    if moov_off is not None:
        adjust_stco_co64(new_mp4, moov_off, delta)

    return bytes(new_mp4)
