from pathlib import Path
from typing import List, Optional

from .ico._core import (
    extract_best_png_from_ico,
    build_plain_ico_block,
)
from .mp4._core import (
    read_box,
    rehead_mp4_with_overlay_and_ftyp,
)
from .zip._core import (
    merge_zip_archives_to_bytes,
    patch_zip_for_prepend,
)

def _normalize_layout(want_ico: bool, want_mp4: bool, want_zip: bool) -> str:
    """
    Byte order:
      - MP4+ICO(+ZIP): [overlay256][ftyp32][mp4_remainder] + [zip?] + [png]
      - MP4(+ZIP):     [mp4] + [zip?]
      - ICO(+ZIP):     [ico(22) + png] + [zip?]
      - ZIP only:      [zip]
    """
    if want_mp4 and want_ico:
        return "OVERLAY_MP4_FIRST"
    if want_mp4 and not want_ico:
        return "MP4_FIRST"
    if want_ico and not want_mp4:
        return "ICO_FIRST"
    return "ZIP_ONLY"

def build_auto(
    output_path: str,
    ico_path: Optional[str],
    mp4_path: Optional[str],
    zip_paths: List[str],
):
    wants_ico = bool(ico_path)
    wants_mp4 = bool(mp4_path)
    wants_zip = bool(zip_paths)

    if wants_zip and len(zip_paths) > 1:
        pass
    else:
        if sum([wants_ico, wants_mp4, wants_zip]) < 2:
            raise ValueError("At least two of (ico, mp4, zip) must be provided.")

    if ico_path and not Path(ico_path).exists():
        raise FileNotFoundError(f"ICO file not found: {ico_path}")
    if mp4_path and not Path(mp4_path).exists():
        raise FileNotFoundError(f"MP4 file not found: {mp4_path}")
    if any(not Path(zip_path).exists() for zip_path in zip_paths):
        raise FileNotFoundError(f"One or more ZIP files not found: {zip_paths}")


    mode = _normalize_layout(wants_ico, wants_mp4, wants_zip)
    out = bytearray()

    if mode == "OVERLAY_MP4_FIRST": # [overlay256][ftyp32][mp4_remainder] + [zip?] + [png]
        png_bytes, w, h = extract_best_png_from_ico(ico_path)

        mp4_bytes = Path(mp4_path).read_bytes()
        fb = read_box(mp4_bytes, 0)
        if not fb:
            raise RuntimeError("Invalid MP4: no top-level box at offset 0")
        original_first_size = fb[0]
        mp4_part_size = 256 + 32 + (len(mp4_bytes) - original_first_size)

        zip_patched = b""
        if wants_zip:
            zip_merged = merge_zip_archives_to_bytes(zip_paths)
            zip_patched = patch_zip_for_prepend(zip_merged, delta=mp4_part_size)

        png_offset_absolute = mp4_part_size + len(zip_patched)
        mp4_part = rehead_mp4_with_overlay_and_ftyp(
            mp4_bytes,
            len(png_bytes),
            (w, h),
            png_offset_absolute,
        )

        out += mp4_part
        if wants_zip:
            out += zip_patched
        out += png_bytes

        Path(output_path).write_bytes(out)
        return
    
    if mode == "MP4_FIRST": # [mp4] + [zip?]
        mp4_bytes = Path(mp4_path).read_bytes()
        out += mp4_bytes
        if wants_zip:
            zip_merged = merge_zip_archives_to_bytes(zip_paths)
            out += patch_zip_for_prepend(zip_merged, delta=len(mp4_bytes))
        Path(output_path).write_bytes(out)
        return
    
    if mode == "ICO_FIRST": # [ico(22) + png] + [zip?]
        png_bytes, w, h = extract_best_png_from_ico(ico_path)
        ico_plain = build_plain_ico_block(len(png_bytes), w, h)
        out += ico_plain
        out += png_bytes
        if wants_zip:
            zip_merged = merge_zip_archives_to_bytes(zip_paths)
            out += patch_zip_for_prepend(zip_merged, delta=len(out))
        Path(output_path).write_bytes(out)
        return
    
    if mode == "ZIP_ONLY": # [zip]
        zip_merged = merge_zip_archives_to_bytes(zip_paths)
        Path(output_path).write_bytes(zip_merged)
        return
    
    raise RuntimeError(f"Nothing to build.")
