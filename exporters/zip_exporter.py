from pathlib import Path
import zipfile

from ..manuscript import Manuscript


def export(manuscript: Manuscript, zip_path: str) -> Path:
    """Zip all original source files from a manuscript into the output directory."""
    if not getattr(manuscript, "original_files", None):
        return None

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for original_file in manuscript.original_files:
            archive.write(original_file, original_file.name)
