from pathlib import Path
import logging
import subprocess
import os
from collections.abc import Iterable

from manuscript import Manuscript

# TODO: this is a bit ugly, maybe the markdown conversion functionality should be in some common utils, so exporters
# don't need to import one another.
import markdown_exporter_innards

# Bits of text we need to replace in the template:
COVER_FILE_LOCATION = "COVER_FILE_HERE"
TITLE_LOCATION = "TITLE_HERE"
LATEX_FILE_LOCATION = "LATEX_FILE_HERE"
ILLUSTRATIONS_FOLDER_LOCATION = "ILLUSTRATIONS_FOLDER_HERE"
DATE_LOCATION = "DATE_HERE"
AUTHOR_LOCATION = "AUTHOR_HERE"
BABEL_LANGUAGE_LOCATION = "BABEL_LANGUAGE_HERE"

# The command that includes the cover, only to be included in the output latex if a cover is supplied, and an
# alternative in case there is no cover.
# TODO: this is too much LaTeX here, this sort of thing should be in the template.
COVER_FILE_LATEX_COMMAND = r"\includegraphics[width=\textwidth]{COVER_FILE_HERE}\\"
NO_COVER_FILE_LATEX_COMMAND = r"~\\\vspace{5cm}"


logger = logging.getLogger(__name__)


def tidy_up_output_dir(out_directory: Path) -> None:
    """Makes sure the output directory is usable.

    (Ended up just being about creating it if needed.)
    """
    if not out_directory.exists():
        logger.info("Output directory at:")
        logger.info(out_directory)
        logger.info("does not exist, so we're gonna create it.")
        out_directory.mkdir()
        return


def build_latex(latex_file: Path, out_directory: Path) -> None:
    """Calls pdflatex to build the given file in the given directory
    """
    if not out_directory.exists():
        logger.error("Output directory does not exist!")
        raise ValueError

    # TODO: we're using os here, but pathlib probably does all of this.
    old_working_dir = os.getcwd()
    os.chdir(out_directory)

    logger.info(f"CD-ing out of {old_working_dir}")
    logger.info(f"... and into {out_directory}")

    pdflatex_cmd = ["pdflatex",
                    "-jobname=" + latex_file.stem,
                    "-interaction=batchmode",
                    "-halt-on-error",
                    "-file-line-error",
                    str(latex_file)]

    # Run subprocess twice so the ToC gets compiled
    logger.info("Calling pdflatex!")
    logger.info(f"Command: {pdflatex_cmd}")
    logger.info("Brace for lots of terminal noise...")
    print("=======================================================================================")
    subprocess.run(pdflatex_cmd, check=True)
    subprocess.run(pdflatex_cmd, check=True)
    print("=======================================================================================")

    logger.info(f"CD-ing out of {os.getcwd()}")
    logger.info(f"... and into {old_working_dir}")
    os.chdir(old_working_dir)


def load_contents_onto_template(latex_contents: str,
                                config: Manuscript.Config,
                                template: Path,
                                illustration_dir: Path,
                                babel_language: str) -> Iterable[str]:
    """Writes the given latex-valid contents into the given template, making replacements where needed.
    """
    output = []

    with template.open("r", encoding="utf8") as temp:
        for template_line in temp:
            if COVER_FILE_LOCATION in template_line:
                # If there is no cover in the config, this line is simply ignored.
                if config.cover:
                    cover_file_command = COVER_FILE_LATEX_COMMAND.replace(COVER_FILE_LOCATION, config.cover)
                    output.append(template_line.replace(COVER_FILE_LOCATION, cover_file_command))
                else:
                    output.append(template_line.replace(COVER_FILE_LOCATION, NO_COVER_FILE_LATEX_COMMAND))

            elif TITLE_LOCATION in template_line:
                output.append(template_line.replace(TITLE_LOCATION, config.title))

            elif ILLUSTRATIONS_FOLDER_LOCATION in template_line:
                output.append(template_line.replace(ILLUSTRATIONS_FOLDER_LOCATION, illustration_dir.as_posix()))

            elif LATEX_FILE_LOCATION in template_line:
                output.append(latex_contents)

            elif DATE_LOCATION in template_line:
                output.append(template_line.replace(DATE_LOCATION, config.time.replace(microsecond=0).isoformat()))

            elif AUTHOR_LOCATION in template_line:
                output.append(template_line.replace(AUTHOR_LOCATION, config.author))

            elif BABEL_LANGUAGE_LOCATION in template_line:
                output.append(template_line.replace(BABEL_LANGUAGE_LOCATION, babel_language))

            else:
                output.append(template_line)

    return output


def convert_to_latex(manuscript: Manuscript) -> str:
    """Converts the content of the Manuscript into a string that is valid LaTeX.

    The output will contain line breaks where necessary; should not be necessary to add them anywhere else.

    I've never publicly admitted to being an excellent programmer, but I have on several occasions admitted to being
    lazy. I don't really, _really_ have a strong desire to write my own markdown-to-latex converter, as much as I love
    latex, because that sounds like an absolute pain in the arse, and a rabbit hole I would not likely emerge from
    unscathed.

    As such, we shall use pandoc.

    Now, in my defense, I'm pushing the whole thing via stdin/stdout, which at the very least should save some mass
    storage calls. Maybe. Probably.
    """
    # Start by converting the content to valid markdown, to feed into... something else.
    markdown_content = markdown_exporter_innards.convert_content_to_lines(manuscript.content)
    pandoc_input = markdown_exporter_innards.concatenate_content_lines_into_string(markdown_content).encode('utf-8')

    pandoc_cmd = ["pandoc",
                  "-r", "markdown-auto_identifiers",
                  "-f", "markdown",
                  "-t", "latex",
                  "--top-level-division=part",
                  "--wrap=preserve"]

    # Cross fingers
    output = subprocess.run(pandoc_cmd,
                            check=True,
                            input=pandoc_input,
                            capture_output=True)

    # stdout is always bytes, so we need to decode it. Input went in as utf-8, so surely the output will come out the
    # same way.
    decoded_output = output.stdout.decode("utf-8")
    return decoded_output


def write_latex_file(full_latex: Iterable[str], out_filename: Path, out_directory: Path) -> None:
    """Takes a list of strings and dumps them into a valid latex file.
    """
    # TODO: we're using os here, but pathlib probably does all of this.
    old_working_dir = os.getcwd()
    os.chdir(out_directory)
    logger.info(f"CD-ing out of {old_working_dir}")
    logger.info(f"... and into {out_directory}")

    with out_filename.open("w", encoding="utf8") as out_file:
        for line in full_latex:
            out_file.write(line)

    logger.info(f"CD-ing out of {os.getcwd()}")
    logger.info(f"... and into {old_working_dir}")
    os.chdir(old_working_dir)
