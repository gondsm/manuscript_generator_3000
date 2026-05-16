from pathlib import Path
import logging

def find_cover_directory(root_folder: Path, cover_name: str) -> Path:
    """Find the directory containing the configured cover file.
    
    In fact, this will find any file with any name, but the plan is to narrow this down and make it faster.
    """
    if not cover_name:
        return Path()

    cover_basename = Path(cover_name).name

    root_matches = [path for path in root_folder.rglob(cover_basename) if path.is_file()]
    if not root_matches:
        logging.error(f"No cover file named {cover_basename} found in root; covers will not be included.")
        return Path()
    
    if len(root_matches) == 1:
        return root_matches[0].parent
    
    if len(root_matches) > 1:
        logging.warning(f"Found multiple cover files named {cover_basename} in root; using {root_matches[0]}.")
        return root_matches[0].parent