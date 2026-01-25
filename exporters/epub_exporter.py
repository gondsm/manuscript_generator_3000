from pathlib import Path
import subprocess
import logging
from textwrap import dedent
import os

from ..manuscript import Manuscript
from . import markdown_exporter_innards

logger = logging.getLogger(__name__)

PANDOC_CSS = dedent("""
    /* Page break before each top-level section */
    section.level1 {
        page-break-before: always;
        break-before: page;
    }

    /* Page break after the section title */
    section.level1 > h1 {
        page-break-after: always;
        break-after: page;
        text-align: center;
        margin-top: 40vh;
        margin-bottom: 0;
    }

""").strip()

TEMP_CSS_FILE = "./temp.css"


def export(manuscript: Manuscript,
           illustration_dir: Path,
           out_file: Path) -> None:
    """A (very) simple epub exporter.

    Requires that pandoc be in the PATH.

    Note:
    * illustration_dir should contain any pictures included in the text (namely the cover specified in manuscript).
    * out_file will be used as the file to output the epub into.
    starts.
    """
    markdown_content = markdown_exporter_innards.convert_content_to_lines(manuscript)
    pandoc_input = markdown_exporter_innards.concatenate_content_lines_into_string(markdown_content).encode('utf-8')

    # So here's the deal: I couldn't find a way to have parts with a clear page that didn't involve CSS. Now I bucket
    # CSS into the same realm as all those new-fangled things that kids these days are doing with the interwebs, and
    # thus have a bit of a visceral desire never to touch it. With pandoc forcing my hand, however, I tried to keep
    # it circumscribed, lest my mind be taken over by the idea of centring divs or something. SO! CSS is written out
    # to a temporary file, which is nuked right after pandoc is called. This also gives me a nice, neat way of
    # adding more CSS later if I need to. Oh how the mighty have fallen.
    with open(TEMP_CSS_FILE, "w", encoding="utf-8") as f:
        f.write(PANDOC_CSS)

    # This whole thing revolves around pandoc
    pandoc_cmd = ["pandoc",
                  "-f", "markdown",
                  "-t", "epub",
                  "--number-sections",
                  "--top-level-division=chapter",
                  f"--metadata=title:{manuscript.config.title}",
                  f"--metadata=author:{manuscript.config.author}",
                  f"--metadata=date:{manuscript.config.time}",
                  "-o", str(out_file),
                  f"--css", TEMP_CSS_FILE]

    # Add a cover if it exists
    if manuscript.config.cover:
        pandoc_cmd.extend(["--epub-cover-image", str(illustration_dir / manuscript.config.cover)])

    logging.info("Executing pandoc with the following command:")
    logging.info(" ".join(pandoc_cmd))

    # Cross fingers
    try:
        subprocess.run(pandoc_cmd,
                       input=pandoc_input,
                       check=True,
                       capture_output=True)
    except subprocess.CalledProcessError as e:
        print("Command failed with return code", e.returncode)
        print("stdout:", e.stdout.decode('utf-8') if e.stdout else "")
        print("stderr:", e.stderr.decode('utf-8') if e.stderr else "")

    if os.path.exists(TEMP_CSS_FILE):
            os.remove(TEMP_CSS_FILE)
