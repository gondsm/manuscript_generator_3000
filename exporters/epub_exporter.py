from pathlib import Path
import subprocess
import logging

from ..manuscript import Manuscript
from . import markdown_exporter_innards

logger = logging.getLogger(__name__)


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

    # TODO: for the moment, we don't support parts when exporting to epub, we we tell the markdown side of the exporter
    # to straight-up ignore them.
    markdown_content = markdown_exporter_innards.convert_content_to_lines(manuscript.content, ignore_parts=True)
    pandoc_input = markdown_exporter_innards.concatenate_content_lines_into_string(markdown_content).encode('utf-8')

    # This whole thing revolves around pandoc
    pandoc_cmd = ["pandoc",
                  "-f", "markdown",
                  "-t", "epub",
                  "--number-sections",
                  f"--metadata=title:{manuscript.config.title}",
                  f"--metadata=author:{manuscript.config.author}",
                  f"--metadata=date:{manuscript.config.time}",
                  "-o", str(out_file)]

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
