from pathlib import Path
import logging
import datetime
from collections.abc import Iterable
import copy
from enum import Enum

from ..manuscript import Manuscript
from ..word_count.word_count import count_words

logger = logging.getLogger(__name__)


# Define delimiter modes
class DelimiterMode(Enum):
    """This script can deal with two kinds of delimiters, essentially how files and config are expected to look in guide
       and index files.

       TASK mode means the initial `- [ ]` syntax.
       EMOJI mode means the new, simple list `- 📚 ` syntax.
    """
    TASK = 1,
    EMOJI = 2


# These constants define the language that this parser accepts.
# TODO: these should probably be configurable
PART_INDICATOR = "-- Part"
CHAPTER_INDICATOR = "-- Chapter"
SCENE_INDICATORS = ["---", "- - -"]

# A preamble is delimited by this sequence at the very top of a file.
PREAMBLE_DELIMITER = "---"

# If a line contains with FILENAME_START (depending on mode) and ends with FILENAME_END, then whatever is in the middle has to be a file in
# the given root folder.
FILENAME_START = {
    DelimiterMode.TASK: "- [ ] [[",
    DelimiterMode.EMOJI: "- 📚 [["
}
FILENAME_END = "]]"

# If a line contains this sequence (depending on mode), then it is a config line of the format
# -- config_key: config_value
CONFIG_START = {
    DelimiterMode.TASK: "- [ ] -- ",
    DelimiterMode.EMOJI: "- 📚 -- "
}
CONFIG_SEPARATOR = ": "

# Part/chapter/etc separator lines can contain inline config
INLINE_CONFIG_START = " -- "
INLINE_CONFIG_SEPARATOR = ": "

# Dictionary keys for parsing out separator config
SEPARATOR_CONFIG_TITLE_KEY = "Title"
SEPARATOR_CONFIG_NUMBERED_KEY = "Numbered"

# Boolean values for separator config
# TODO: this seems excessive. There should be a standard way of converting a string to bool following Python rules (like
# any YAML parser would do, that has to be a thing)
SEPARATOR_CONFIG_TRUE = "True"
SEPARATOR_CONFIG_FALSE = "False"

# Default config for separators
SEPARATOR_CONFIG_DEFAULT = Manuscript.SeparatorConfig("", True)

# And these are the config keys we know about
AUTHOR_KEY = "Author"
TITLE_KEY = "Title"
COVER_KEY = "Cover"
SCENE_SEPARATOR_TYPE_KEY = "Scene Separator"


def extract_relevant_lines_from_index_file(index_file: Path, delimiter_mode: DelimiterMode) -> Iterable[str]:
    """Extracts the relevant text from the given markdown index file.

    Relevant lines are those which contain markers like the start of config or a filename.

    Returns the text verbatim as a list of lines, to be post-processed later.
    """
    lines = []
    with open(index_file, "r", encoding="utf-8") as in_file:
        for line in in_file:
            if line.strip() == "":
                # Disregard empty lines
                continue
            # We only pull in lines that either contain config or file name to include.
            elif CONFIG_START[delimiter_mode] in line or FILENAME_START[delimiter_mode] in line:
                lines.append(line.strip())

    return lines


def _list_markdown_files_in_folder(folder: Path):
    files = []
    for path, _, filenames in folder.walk():
        for filename in filenames:
            if ".md" in filename:
                full_path = path / filename
                files.append(full_path)

    return files


def _find_markdown_file_path(filename: Path, root_folder: Path) -> Path:
    known_files = _list_markdown_files_in_folder(root_folder)

    # Match on the exact file stem rather than a substring of the full path
    matches = [f for f in known_files if f.stem == str(filename)]

    # We build a clear, actionable message for both failure modes and put it on the exception itself.
    if len(matches) == 0:
        message = (
            f"No markdown file found for reference [[{filename}]] under '{root_folder}'. "
            f"Check the index file for a typo or a link to a file that does not exist."
        )
        logger.error(message)
        raise ValueError(message)

    if len(matches) > 1:
        formatted_matches = "\n".join(f"  - {m}" for m in matches)
        message = (
            f"Reference [[{filename}]] under '{root_folder}' ambiguously matches {len(matches)} files:\n"
            f"{formatted_matches}\n"
            f"Rename the file(s) so that exactly one has this stem, or make the reference more specific."
        )
        logger.error(message)
        raise ValueError(message)

    return matches[0]


def _extract_text_from_file(filename: Path, root_folder: Path, ignore_preamble: bool) -> Iterable[str]:
    """Finds the given file in the given folder (or subfolders) and returns its contents as a list of strings.

    If ignore_preamble is set, a properties block at the top of the file is dropped.
    """
    # TODO: bit wasteful to walk the directory for every single call to this function
    full_path = _find_markdown_file_path(filename, root_folder)

    # The preamble can only start on the first (non-empty) line of the file, so we stop looking for it as soon as we
    # come across any other line.
    looking_for_preamble = ignore_preamble
    in_preamble = False

    # TODO: possibly not the best way to go from text file to list of lines.
    output = []
    with open(full_path, "r", encoding="utf-8") as in_file:
        for line in in_file:
            stripped = line.strip()
            if stripped == "":
                # Disregard empty lines
                continue

            if in_preamble:
                if stripped == PREAMBLE_DELIMITER:
                    in_preamble = False
                continue

            if looking_for_preamble:
                looking_for_preamble = False
                if stripped == PREAMBLE_DELIMITER:
                    in_preamble = True
                    continue

            output.append(stripped)

    return output


def count_words_in_lines(lines: Iterable[str]) -> int:
    """Counts the words that a sequence of raw lines contributes to a manuscript.

    Lines that end up as separators (scene breaks and the like) carry no words, so they are left out, which keeps these
    counts consistent with the ones taken from a finished Manuscript.
    """
    return sum([count_words(line) for line in replace_indicators(lines) if not Manuscript.is_control_type(line)])


def extract_text_from_files(lines: Iterable[str], root_folder: Path, delimiter_mode: DelimiterMode,
                            ignore_preamble: bool) -> tuple[Iterable[str], list[Path], list[Manuscript.ChapterContribution]]:
    """Given a sequence of lines as extracted by extract_relevant_section, pull text out of the given filenames.

    This replaces (not in place) every reference to a filename in the lines with a sequence of lines that contain the
    text.

    Returns [lines_with_text, original_files, composition], where the composition describes which files ended up in
    which chapter, and how many words each of them contributed.
    """
    output = []
    original_files = []
    composition = []

    # We keep track of where we are in the manuscript so that every file we load can be attributed to a chapter.
    # Everything starts out negative, as we may well come across files before any separator shows up.
    part_index = -1
    part_title = ""
    chapter_index = -1
    current_chapter = None

    for line in lines:
        if FILENAME_START[delimiter_mode] in line and FILENAME_END in line:
            filename = line.split(FILENAME_START[delimiter_mode])[-1].split(FILENAME_END)[0]
            logger.debug(f"Loading file: {filename}")

            file_path = _find_markdown_file_path(filename, root_folder)
            text = _extract_text_from_file(filename, root_folder, ignore_preamble)

            logger.debug(f"Loaded {len(text)} lines from {file_path}.")

            output.extend(text)
            original_files.append(file_path)

            if current_chapter is None:
                # Text can show up before any chapter separator does, and it still needs a home in the breakdown.
                current_chapter = Manuscript.ChapterContribution(part_index, part_title, chapter_index, "")
                composition.append(current_chapter)

            current_chapter.files.append(Manuscript.FileContribution(file_path, count_words_in_lines(text)))

        else:
            if PART_INDICATOR in line:
                part_index += 1
                part_title = _convert_inline_config_to_separator_config(_extract_inline_config(line)).title
                # Chapters are numbered within their part.
                chapter_index = -1
                current_chapter = None

            elif CHAPTER_INDICATOR in line:
                chapter_index += 1
                chapter_title = _convert_inline_config_to_separator_config(_extract_inline_config(line)).title
                current_chapter = Manuscript.ChapterContribution(part_index, part_title, chapter_index, chapter_title)
                composition.append(current_chapter)

            output.append(line)

    return output, original_files, composition


def replace_indicators(lines: Iterable[str]) -> Manuscript.Content:
    """Replaces the indicators defined above (e.g. PART_INDICATOR) with the separator objects used in Manuscript.

    No other lines are touched. Returns a list that contains strings and separator objects (see Manuscript).
    """
    # TODO: there's an undesirable relationship between this and extract_global_config below. If in SHORT DelimiterMode,
    # it is possible that extract_global_config get rid of the indicators this function uses to create its separator
    # objects. For now, it is CRUCIAL that this function be called befor extract_global_config.
    output = []

    for line in lines:
        if PART_INDICATOR in line:
            separator_config = _convert_inline_config_to_separator_config(_extract_inline_config(line))
            output.append(Manuscript.StartPart(separator_config))

        elif CHAPTER_INDICATOR in line:
            separator_config = _convert_inline_config_to_separator_config(_extract_inline_config(line))
            output.append(Manuscript.StartChapter(separator_config))

        elif any([indicator in line for indicator in SCENE_INDICATORS]):
            output.append(Manuscript.BreakScene())

        else:
            output.append(line)

    return output


def extract_global_config(lines: Manuscript.Content, delimiter_mode: DelimiterMode) -> [Iterable[str], Manuscript.Config]:
    """Extracts the config in the given lines into a dictionary.

    Returns [lines_without_config, config]
    """
    output = []
    config = {}
    for line in lines:
        if Manuscript.is_control_type(line):
            # Lines could have non-string separators at this point, so we just add the line and move on.
            output.append(line)
            continue

        # Config lines always have a -- in them
        if CONFIG_START[delimiter_mode] in line:
            key = line.split(CONFIG_START[delimiter_mode])[-1].split(CONFIG_SEPARATOR)[0].strip()
            value = line.split(CONFIG_SEPARATOR)[-1].strip()
            config[key] = value
        else:
            output.append(line)

    return [output, config]


def _extract_inline_config(line: str) -> dict:
    """Extracts the config that may exist in part/chapter/etc separators.
    """
    output = {}

    # No point in parsing if there's nothing to parse
    if (INLINE_CONFIG_START not in line):
        return output

    # Start by erasing any instances of separators from the line
    trimmed_line = line.replace(PART_INDICATOR, "").replace(CHAPTER_INDICATOR, "")

    # Then we break up the line looking for individual config entries
    for elem in trimmed_line.split(INLINE_CONFIG_START):
        if (INLINE_CONFIG_SEPARATOR in elem):
            key, value = elem.split(INLINE_CONFIG_SEPARATOR)

            if not key or not value:
                logger.warning("Found a strange empty key or value whilst parsing this line. Skipping line.")
                logger.warning(f"Element: {elem}")
                logger.warning(f"Line: {line}")
                continue

            # Strip out extraneous characters before inserting into the dict
            output[key.strip()] = value.strip()

    return output


def _convert_inline_config_to_separator_config(input: dict) -> Manuscript.SeparatorConfig:
    """Converts a dict containing inline config into a SeparatorConfig object.
    """
    output = copy.deepcopy(SEPARATOR_CONFIG_DEFAULT)

    if SEPARATOR_CONFIG_TITLE_KEY in input:
        output.title = input[SEPARATOR_CONFIG_TITLE_KEY]

    if SEPARATOR_CONFIG_NUMBERED_KEY in input:
        value = input[SEPARATOR_CONFIG_NUMBERED_KEY]
        if value == SEPARATOR_CONFIG_TRUE:
            output.numbered = True
        elif value == SEPARATOR_CONFIG_FALSE:
            output.numbered = False
        else:
            logger.warning(f"Found a strange value for the Numbered property: {value}")

    return output


def extract_properties(lines: Iterable[str]):
    """Extracts the config in the given lines into a dictionary, assuming markdown properties as known in Obsidian.

    Returns [lines_without_config, config]

    TODO: What we should _really_ be doing here is extracting the frontmatter and using yaml to load it.
    """
    in_properties = False
    properties_read = False
    config = {}
    output_lines = []
    for i, line in enumerate(lines):
        # Properties _must_ start on the first line of the file.
        if i == 0 and line.strip() == "---" and not in_properties and not properties_read:
            in_properties = True
            continue

        # There can only be one properties block, so if we find this again, we're done.
        if line.strip() == "---" and in_properties:
            in_properties = False
            properties_read = True
            continue

        if line != "\n" and len(line.split(":")) == 2 and in_properties:
            key, value = line.split(":")
            config[key.strip()] = value.strip()
            continue

        output_lines.append(line)

    return [output_lines, config]


def _convert_config_dict_to_object(config: dict) -> Manuscript.Config:
    """Converts a config dictionary as returned from extract_config into a Manuscript.Config.

    Uses the constants at the top of the file to do all necessary conversions.
    """
    author = "unnamed author"
    title = "untitled"
    cover = ""
    scene_separator_type = "normal"

    if AUTHOR_KEY in config:
        author = config[AUTHOR_KEY]
        logger.info("Adding author to config: {author}")

    if TITLE_KEY in config:
        title = config[TITLE_KEY]
        logger.info(f"Adding title to config: {title}")

    if COVER_KEY in config:
        cover = config[COVER_KEY]
        logger.info(f"Adding cover to config: {cover}")

    if SCENE_SEPARATOR_TYPE_KEY in config:
        scene_separator_type = config[SCENE_SEPARATOR_TYPE_KEY]
        logger.info(f"Adding scene separator type to config: {scene_separator_type}")

    time = datetime.datetime.now()
    logger.info(f"Adding time to config: {time}")

    return Manuscript.Config(title, author, cover, time, scene_separator_type)


def construct_manuscript(parsed_lines: Iterable[str], config: dict, original_files: list[Path] | None = None,
                         composition: list[Manuscript.ChapterContribution] | None = None) -> Manuscript:
    """Takes a list of parsed lines and a config dict and constructs a Manuscript object.

    The lines MUST have been stripped of config, had any indicators replaced, etc.
    config should be in the format returned by extract_config.
    """
    return Manuscript(parsed_lines, _convert_config_dict_to_object(config), original_files or [], composition or [])
