from pathlib import Path
import logging

from . import markdown_importer_innards as innards
from ..manuscript import Manuscript

logger = logging.getLogger(__name__)


def load_manuscript_from_file(filename: Path, root_folder: Path) -> Manuscript:
    # TODO: logging

    # The order actually matters, here, because if we replace the indicators before pulling the properties, the property
    # indicators and scene breaks get confused as Obsidian uses the same sequence of chars for both.
    full_path = innards._find_markdown_file_path(filename, root_folder)
    lines_with_text = innards._extract_text_from_file(filename, root_folder, ignore_preamble=False)
    parsed_lines, config = innards.extract_properties(lines_with_text)
    lines_with_correct_indicators = innards.replace_indicators(parsed_lines)

    # A single-file manuscript has no parts or chapters to speak of, but it is still worth knowing where its words came
    # from, so we describe it as one nameless chapter made up of the one file.
    composition = [Manuscript.ChapterContribution(-1, "", -1, "",
                                                  [Manuscript.FileContribution(full_path,
                                                                               innards.count_words_in_lines(parsed_lines))])]

    manuscript = innards.construct_manuscript(lines_with_correct_indicators, config, [full_path], composition)

    return manuscript