from pathlib import Path
import logging
import datetime
from collections.abc import Iterable

from manuscript import Manuscript

logger = logging.getLogger(__name__)

# These constants define the language that this parser accepts.
# TODO: these should probably be configurable
PART_INDICATOR = "-- Part"
CHAPTER_INDICATOR = "-- Chapter"
PROLOGUE_INDICATOR = "-- Prologue"
SCENE_INDICATORS = ["---", "- - -"]

# If a line contains with FILENAME_START and ends with FILENAME_END, then whatever is in the middle has to be a file in
# the given root folder.
FILENAME_START = "- [ ] [["
FILENAME_END = "]]"

# If a line contains this sequence, then it is a config line of the format
# -- config_key: config_value
CONFIG_START = "- [ ] -- "
CONFIG_SEPARATOR = ": "

# And these are the config keys we know about
AUTHOR_KEY = "Author"
TITLE_KEY = "Title"
COVER_KEY = "Cover"


def extract_relevant_section(guide_file: Path, subheading: str) -> Iterable[str]:
    """Extracts the relevant text from the given markdown subheading.

    Returns the text verbatim as a list of lines, to be post-processed later.
    """
    lines = []
    in_region_of_interest = False
    with open(guide_file, "r", encoding="utf-8") as in_file:
        for line in in_file:
            if line[0:3] == "## " and subheading in line:
                logger.info(f"Found the relevant subheading for {subheading} at this line:")
                logger.info(line.strip())
                in_region_of_interest = True
                continue
            elif line.strip() == "":
                # Disregard empty lines
                continue
            elif line[0:3] == "## " and in_region_of_interest:
                in_region_of_interest = False
                break
            # We only pull in lines that either contain config or file name to include.
            elif in_region_of_interest and (CONFIG_START in line or FILENAME_START in line):
                lines.append(line)

    return lines


def extract_relevant_lines_from_index_file(index_file: Path) -> Iterable[str]:
    """Similar to extract_relevant_section, but from an index file instead of a guide file.

    Since an index file won't have subheadings (it will represent a single manuscript), we need only to pull in all
    lines that contain either config or files to include.
    """
    lines = []
    with open(index_file, "r", encoding="utf-8") as in_file:
        for line in in_file:
            if line.strip() == "":
                # Disregard empty lines
                continue
            # We only pull in lines that either contain config or file name to include.
            elif CONFIG_START in line or FILENAME_START in line:
                lines.append(line)

    return lines


def list_markdown_files_in_folder(folder: Path):
    files = []
    for path, _, filenames in folder.walk():
        for filename in filenames:
            if ".md" in filename:
                full_path = path / filename
                files.append(full_path)

    return files


def extract_text_from_file(filename: Path, root_folder: Path) -> Iterable[str]:
    """Finds the given file in the given folder (or subfolders) and returns its contents as a list of strings.
    """
    # TODO: bit wasteful to walk the directory for every single call to this function
    known_files = list_markdown_files_in_folder(root_folder)

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


def extract_text_from_files(lines: Iterable[str], root_folder: Path) -> Iterable[str]:
    """Given a sequence of lines as extracted by extract_relevant_section, pull text out of the given filenames.

    This replaces (not in place) every reference to a filename in the lines with a sequence of lines that contain the
    text.
    """
    output = []
    for line in lines:
        if FILENAME_START in line and FILENAME_END in line:
            filename = line.split(FILENAME_START)[-1].split(FILENAME_END)[0]
            logger.debug(f"Loading file: {filename}")

            text = extract_text_from_file(filename, root_folder)

            logger.debug(f"Loaded {len(text)} lines.")

            output.extend(text)

        else:
            output.append(line)

    return output


def replace_indicators(lines: Iterable[str]) -> Iterable[str]:
    """Replaces the indicators defined above (e.g. PART_INDICATOR) with those used by Manuscript.

    No other lines are touched. Returns a new list, the param is not touched.
    """
    output = []

    for line in lines:
        if PROLOGUE_INDICATOR in line:
            output.append(Manuscript.START_PROLOGUE)

        elif PART_INDICATOR in line:
            output.append(Manuscript.START_PART)

        elif CHAPTER_INDICATOR in line:
            output.append(Manuscript.START_CHAPTER)

        elif any([indicator in line for indicator in SCENE_INDICATORS]):
            output.append(Manuscript.BREAK_SCENE)

        else:
            output.append(line)

    return output


def extract_config(lines: Iterable[str]) -> [Iterable[str], Manuscript.Config]:
    """Extracts the config in the given lines into a dictionary.

    Returns [lines_without_config, config]
    """
    output = []
    config = {}
    for line in lines:
        # Config lines always have a -- in them
        if CONFIG_START in line:
            key = line.split(CONFIG_START)[-1].split(CONFIG_SEPARATOR)[0].strip()
            value = line.split(CONFIG_SEPARATOR)[-1].strip()
            config[key] = value
        else:
            output.append(line)

    return [output, config]


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


def convert_config_dict_to_object(config: dict) -> Manuscript.Config:
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
    return Manuscript(parsed_lines, convert_config_dict_to_object(config))
