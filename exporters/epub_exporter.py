from pathlib import Path
import subprocess
import logging

from ..manuscript import Manuscript
from . import markdown_exporter_innards

logger = logging.getLogger(__name__)


def manually_number_markdown(markdown_lines):
    """Processes a list of markdown lines to manually number parts and chapters, while marking all sections as unnumbered for pandoc.
    
    This function ensures that parts and chapters in the manuscript get custom numbering in their titles,
    while preventing pandoc from applying its own automatic numbering to any sections. It respects
    existing {.unnumbered} markers on headers, leaving them untouched.

    This isn't just me being a silly bean and writing up unnecessary code to maintain. The root issue here is that LaTeX and pandoc have
    different opinions on how to number sections, and we want to keep them consistent across both. With this in place, we can have the
    same config for both exporters in the index file, and expect the same numbering in both outputs, rather than pandoc going a bit
    crazy with the numbering on the epub. In practice, this is a (bad) port of the LaTeX numbering rules.
    
    We respect {.unnumbered}.
    """
    part_counter = 0
    chapter_counter = 0
    result = []
    
    for line in markdown_lines:
        stripped = line.lstrip()
        if stripped.startswith('#'):
            # Parse out the level we're at
            level = 0
            while level < len(stripped) and stripped[level] == '#':
                level += 1
            title = stripped[level:].strip()
            hashes = '#' * level
            
            # Respect unnumbered
            is_unnumbered = '{.unnumbered}' in title
            if is_unnumbered:
                # Respect the unnumbered marker, don't add manual numbers or {-}
                new_line = f"{hashes} {title}"

            # Apply the correct numbering and level.
            elif level == 1:
                part_counter += 1
                chapter_counter = 0  # reset chapter counter for new part
                new_line = f"{hashes} {part_counter}. {title} {{-}}"
            elif level == 2:
                chapter_counter += 1
                new_line = f"{hashes} {chapter_counter} {title} {{-}}"
            
            result.append(new_line)
        else:
            result.append(line)
    
    return result


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
    
    post_processed_markdown = manually_number_markdown(markdown_content)
    
    pandoc_input = markdown_exporter_innards.concatenate_content_lines_into_string(post_processed_markdown).encode('utf-8')

    # This whole thing revolves around pandoc
    pandoc_cmd = ["pandoc",
                  "-f", "markdown",
                  "-t", "epub",
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
