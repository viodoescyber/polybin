import io
import struct
from typing import Tuple
from PIL import Image

def extract_best_png_from_ico(ico_path: str) -> Tuple[bytes, int, int]:
    """Extract the largest frame from ICO as PNG (lossless)."""
    im = Image.open(ico_path)
    try:
        n = im.n_frames
    except Exception:
        n = 1

    best_idx, best_area = 0, -1
    for i in range(n):
        try:
            im.seek(i)
        except EOFError:
            break
        w, h = im.size
        area = w * h
        if area > best_area:
            best_area = area
            best_idx = i

    im.seek(best_idx)
    frame = im.convert("RGBA")
    w, h = frame.size
    buf = io.BytesIO()
    frame.save(buf, format="PNG", optimize=False)
    im.close()
    return buf.getvalue(), w, h

def build_plain_ico_block(png_size: int, width_px: int, height_px: int) -> bytes:
    """
    Standard ICO header (6) + one entry (16) where ImageOffset=22 so PNG follows immediately.
    """
    header = struct.pack("<HHH", 0, 1, 1)
    w_byte = 0 if width_px >= 256 else (width_px & 0xFF)
    h_byte = 0 if height_px >= 256 else (height_px & 0xFF)
    entry = struct.pack(
        "<BBBBHHII",
        w_byte,  # width
        h_byte,  # height
        0,       # colors
        0,       # reserved
        1,       # planes
        32,      # bitcount
        png_size,  # BytesInRes
        22,        # ImageOffset (6+16)
    )
    return header + entry

def build_overlay_ico_head_256(
    png_size: int, png_offset_abs: int, width_px: int, height_px: int
) -> bytes:
    """
    256-byte MP4 box whose payload is a valid ICO header + entry pointing to a PNG
    at absolute offset 'png_offset_abs'.
    """
    box = bytearray(256)
    # MP4 box size (big-endian)
    box[0:4] = struct.pack(">I", 256)
    # ICO count (LE) = 1
    box[4:6] = (1).to_bytes(2, "little")
    # ICO width/height (0 means 256)
    box[6] = 0 if width_px >= 256 else (width_px & 0xFF)
    box[7] = 0 if height_px >= 256 else (height_px & 0xFF)
    # ColorCount, Reserved
    box[8] = 0
    box[9] = 0
    # Planes (1), BitCount (32)
    box[10:12] = (1).to_bytes(2, "little")
    box[12:14] = (32).to_bytes(2, "little")
    # BytesInRes (PNG size), ImageOffset (absolute)
    box[14:18] = (png_size).to_bytes(4, "little")
    box[18:22] = (png_offset_abs).to_bytes(4, "little")
    return bytes(box)
