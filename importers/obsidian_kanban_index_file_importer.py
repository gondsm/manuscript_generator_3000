from pathlib import Path
import logging

from . import obsidian_kanban_subheading_importer_innards as innards
from ..manuscript import Manuscript

logger = logging.getLogger(__name__)


def load_manuscript_from_index_file(index_file: Path, root_folder: Path) -> Manuscript:
    """This importer is very similar to the obsidian_kanban_heading_importer, but instead of loading from a sub-heading
    in a guide file, it loads a manuscript from an index file.

    An index file follows the same structure as a subheading in a guide file, only the whole file is considered
    "relevant" for the manuscript.
    """

    logger.info("Loading Manuscript from Heading File.")
    logger.info(f"Index file: {index_file}")
    logger.info(f"Root folder: {root_folder}")

    # Check whether file exists
    if not index_file.exists():
        logger.error("File does not exist!")
        return None

    # Pull the section of Markdown that encodes the manuscript from the given file
    logger.info("Reading lines from file.")
    raw_lines = innards.extract_relevant_lines_from_index_file(index_file)
    logger.info(f"Extracted index with {len(raw_lines)} lines.")

    logger.info("Extracting text from files.")
    lines_with_text = innards.extract_text_from_files(raw_lines, root_folder)

    logger.info("Replacing text indicators with Manuscript indicators.")
    lines_with_correct_indicators = innards.replace_indicators(lines_with_text)

    logger.info("Extracting config.")
    parsed_lines, config = innards.extract_global_config(lines_with_correct_indicators)

    logger.info("Constructing Manuscript object.")
    manuscript = innards.construct_manuscript(parsed_lines, config)
    return manuscript
