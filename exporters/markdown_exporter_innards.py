import dataclasses
from pathlib import Path
from collections.abc import Iterable

from ..manuscript import Manuscript

MD_PART_SEPARATOR = "#"
MD_CHAPTER_SEPARATOR = "##"
MD_SCENE_SEPARATOR = "---"
MD_UNNUMBERED_INDICATOR = "{.unnumbered}"


def convert_config_to_md_properties(config: Manuscript.Config) -> Iterable[str]:
    """Takes a Manuscript.Config and turns it into markdown properties (as understood by Obsidian).

    https://help.obsidian.md/Editing+and+formatting/Properties
    """
    output_lines = []

    output_lines.append("---")

    for field in dataclasses.fields(config):
        value = getattr(config, field.name)
        output_lines.append(f"{field.name}: {value}")

    output_lines.append("---")

    return output_lines


def convert_config_to_markdown(config: Manuscript.SeparatorConfig) -> str:
    output = ""

    # Add title
    output += config.title

    # Optionally signal that this chapter is not numbered
    if not config.numbered:
        output += " "
        output += MD_UNNUMBERED_INDICATOR

    return output


def convert_content_to_lines(content: Manuscript.Content) -> Iterable[str]:
    """Takes the content of a Manuscript and turns into valid lines of Markdown.
    """
    output_lines = []

    for line in content:
        if isinstance(line, Manuscript.StartPart):
            # TODO: Perhaps a helper function?
            converted_line = MD_PART_SEPARATOR + " " + convert_config_to_markdown(line.config)
            output_lines.append(converted_line)
        if isinstance(line, Manuscript.StartChapter):
            # TODO: Perhaps a helper function?
            converted_line = MD_CHAPTER_SEPARATOR + " " + convert_config_to_markdown(line.config)
            output_lines.append(converted_line)
        elif isinstance(line, Manuscript.BreakScene):
            output_lines.append(MD_SCENE_SEPARATOR)
        else:
            output_lines.append(line)

    return output_lines


def concatenate_content_lines_into_string(content: Iterable[str]) -> str:
    """Concatenates valid markdown lines into a single markdown string.
    """
    return "\n\n".join(content)


def write_to_file(properties: Iterable[str], content: Manuscript.Content, out_file: Path) -> None:
    """Takes the properties and Markdown content, and writes it into the given file.
    """
    with open(out_file, "w", encoding="utf-8") as out:
        out.write("\n".join(properties))
        out.write("\n\n")
        out.write(concatenate_content_lines_into_string(content))
        out.write("\n")
