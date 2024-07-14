import dataclasses
from pathlib import Path
from collections.abc import Iterable

from manuscript import Manuscript

# TODO: little bit of portuguese here
MD_PROLOGUE_SEPARATOR = "## Prólogo {.unnumbered}"
MD_PART_SEPARATOR = "#"
MD_CHAPTER_SEPARATOR = "##"
MD_SCENE_SEPARATOR = "---"


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


def convert_content_to_lines(content: Iterable[str]) -> Iterable[str]:
    """Takes the content of a Manuscript and turns into valid lines of Markdown.
    """
    output_lines = []

    for line in content:
        if line == Manuscript.START_PART:
            output_lines.append(MD_PART_SEPARATOR)
        elif line == Manuscript.START_PROLOGUE:
            output_lines.append(MD_PROLOGUE_SEPARATOR)
        elif line == Manuscript.START_CHAPTER:
            output_lines.append(MD_CHAPTER_SEPARATOR)
        elif line == Manuscript.BREAK_SCENE:
            output_lines.append(MD_SCENE_SEPARATOR)
        else:
            output_lines.append(line)

    return output_lines


def concatenate_content_lines_into_string(content: Iterable[str]) -> str:
    """Concatenates valid markdown lines into a single markdown string.
    """
    return "\n\n".join(content)


def write_to_file(properties: Iterable[str], content: Iterable[str], out_file: Path) -> None:
    """Takes the properties and Markdown content, and writes it into the given file.
    """
    with open(out_file, "w", encoding="utf-8") as out:
        out.write("\n".join(properties))
        out.write("\n\n")
        out.write(concatenate_content_lines_into_string(content))
        out.write("\n")
