from pathlib import Path
import logging

from . import obsidian_kanban_subheading_importer_innards as innards
from ..manuscript import Manuscript

logger = logging.getLogger(__name__)


def load_manuscript_from_file(filename: Path, root_folder: Path) -> Manuscript:
    # TODO: logging

    # The order actually matters, here, because if we replace the indicators before pulling the properties, the property
    # indicators and scene breaks get confused as Obsidian uses the same sequence of chars for both.
    lines_with_text = innards.extract_text_from_file(filename, root_folder)
    parsed_lines, config = innards.extract_properties(lines_with_text)
    lines_with_correct_indicators = innards.replace_indicators(parsed_lines)
    manuscript = innards.construct_manuscript(lines_with_correct_indicators, config)

    return manuscript