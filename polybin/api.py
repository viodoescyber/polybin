from typing import List, Optional
from .builders import build_auto

def build(
    output_path: str,
    ico_path: Optional[str] = None,
    mp4_path: Optional[str] = None,
    zip_paths: Optional[List[str]] = None,
):
    """
    Public API: Auto-detect combination from provided paths.
    """
    zip_paths = zip_paths or []
    build_auto(
        output_path=output_path,
        ico_path=ico_path,
        mp4_path=mp4_path,
        zip_paths=zip_paths,
    )
    