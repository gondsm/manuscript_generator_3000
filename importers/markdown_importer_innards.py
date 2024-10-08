from pathlib import Path
import logging
import datetime
from collections.abc import Iterable
import copy
from enum import Enum

from ..manuscript import Manuscript

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


def _extract_text_from_file(filename: Path, root_folder: Path) -> Iterable[str]:
    """Finds the given file in the given folder (or subfolders) and returns its contents as a list of strings.
    """
    # TODO: bit wasteful to walk the directory for every single call to this function
    known_files = _list_markdown_files_in_folder(root_folder)

    # Extract the complete path from the known files
    # TODO: going from a pathlib object to string is a bit meh, surely pathlib has a cooler way of doing this.
    full_path = [f for f in known_files if filename in str(f)]

    if len(full_path) != 1:
        logger.error(f"Found an unexpected amount of full paths for filename {filename}!")
        logger.error(f"Found: {full_path}")
        raise ValueError

    full_path = full_path[0]

    # TODO: possibly not the best way to go from text file to list of lines.
    output = []
    with open(full_path, "r", encoding="utf-8") as in_file:
        for line in in_file:
            stripped = line.strip()
            if stripped == "":
                # Disregard empty lines
                continue

            output.append(stripped)

    return output


def extract_text_from_files(lines: Iterable[str], root_folder: Path, delimiter_mode: DelimiterMode) -> Iterable[str]:
    """Given a sequence of lines as extracted by extract_relevant_section, pull text out of the given filenames.

    This replaces (not in place) every reference to a filename in the lines with a sequence of lines that contain the
    text.
    """
    output = []
    for line in lines:
        if FILENAME_START[delimiter_mode] in line and FILENAME_END in line:
            filename = line.split(FILENAME_START[delimiter_mode])[-1].split(FILENAME_END)[0]
            logger.debug(f"Loading file: {filename}")

            text = _extract_text_from_file(filename, root_folder)

            logger.debug(f"Loaded {len(text)} lines.")

            output.extend(text)

        else:
            output.append(line)

    return output


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
    """
    in_properties = False
    properties_read = False
    config = {}
    output_lines = []
    for line in lines:
        if line.strip() == "---" and not in_properties and not properties_read:
            in_properties = True
            continue

        # There can only be one properties block, so if we find this again, we're done.
        if line.strip() == "---" and in_properties:
            in_properties = False
            properties_read = True
            continue

        if in_properties:
            key, value = line.split(":")
            config[key.strip()] = value.strip()
            continue

        output_lines.append(line)

    logger.info(f"Read properties from file: {config}")

    return [output_lines, config]


def _convert_config_dict_to_object(config: dict) -> Manuscript.Config:
    """Converts a config dictionary as returned from extract_config into a Manuscript.Config.

    Uses the constants at the top of the file to do all necessary conversions.
    """
    author = "unnamed author"
    title = "untitled"
    cover = ""

    if AUTHOR_KEY in config:
        author = config[AUTHOR_KEY]
        logger.info("Adding author to config: {author}")

    if TITLE_KEY in config:
        title = config[TITLE_KEY]
        logger.info(f"Adding title to config: {title}")

    if COVER_KEY in config:
        cover = config[COVER_KEY]
        logger.info(f"Adding cover to config: {cover}")

    time = datetime.datetime.now()
    logger.info(f"Adding time to config: {time}")

    return Manuscript.Config(title, author, cover, time)


def construct_manuscript(parsed_lines: Iterable[str], config: dict) -> Manuscript:
    """Takes a list of parsed lines and a config dict and constructs a Manuscript object.

    The lines MUST have been stripped of config, had any indicators replaced, etc.
    config should be in the format returned by extract_config.
    """
    return Manuscript(parsed_lines, _convert_config_dict_to_object(config))
