from pathlib import Path

import markdown_exporter_innards as innards
from manuscript import Manuscript


def export(manuscript: Manuscript, out_file: Path) -> None:
    """Exports the given Manuscript into the given out_file.
    """
    output_properties = innards.convert_config_to_md_properties(manuscript.config)
    output_content = innards.convert_content_to_lines(manuscript.content)
    innards.write_to_file(output_properties, output_content, out_file)
