from pathlib import Path
import logging

from . import obsidian_kanban_subheading_importer_innards as innards
from ..manuscript import Manuscript

logger = logging.getLogger(__name__)


def load_manuscript_from_subheading(guide_file: Path, subheading: str, root_folder: Path) -> Manuscript:
    """Loads a Manuscript from a subheading in the given guide_file.

    This importer assumes that the manuscript is encoded as a sequence of Obsidian file links in a subheading (as you
    would get if you were to use the kanban plugin with one file link per card, try to guess why that is).
    """

    logger.info("Loading Manuscript from Obsidian Kanban")
    logger.info(f"Guide file: {guide_file}")
    logger.info(f"Subheading: {subheading}")
    logger.info(f"Root folder: {root_folder}")

    # Check whether file exists
    if not guide_file.exists():
        logger.error("File does not exist!")
        return None

    # Pull the section of Markdown that encodes the manuscript from the given file
    logger.info("Reading lines from file.")
    raw_lines = innards.extract_relevant_section(guide_file, subheading)
    logger.info(f"Extracted a relevant section with {len(raw_lines)} lines.")

    logger.info("Extracting text from files.")
    lines_with_text = innards.extract_text_from_files(raw_lines, root_folder)

    logger.info("Replacing text indicators with Manuscript indicators.")
    lines_with_correct_indicators = innards.replace_indicators(lines_with_text)

    logger.info("Extracting config.")
    parsed_lines, config = innards.extract_config(lines_with_correct_indicators)

    logger.info("Constructing Manuscript object.")
    manuscript = innards.construct_manuscript(parsed_lines, config)
    return manuscript
