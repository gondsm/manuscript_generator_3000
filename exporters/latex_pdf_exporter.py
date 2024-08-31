from ..manuscript import Manuscript
from . import latex_pdf_exporter_innards as innards

from pathlib import Path


def export(manuscript: Manuscript,
           template: Path,
           illustration_dir: Path,
           out_directory: Path,
           out_name: str,
           babel_language: str,
           remove_artifacts: bool) -> None:
    """Export the given manuscript to a PDF via LaTeX.

    Requires that pdflatex be in the PATH and accessible by this script.

    Note:
    * illustration_dir should contain any pictures included in the text (namely the cover specified in manuscript).
    * out_directory will be used as an output.
    * If remove_artifacts is set, then at the end this exporter will remove intermediate artifacts.
    * Internally, this exporter relies on pdflatex and pandoc being available in the PATH.
    """
    innards.tidy_up_output_dir(out_directory)
    latex_contents = innards.convert_to_latex(manuscript)
    full_latex = innards.load_contents_onto_template(latex_contents,
                                                     manuscript.config,
                                                     template,
                                                     illustration_dir,
                                                     babel_language)
    innards.write_latex_file(full_latex, out_directory / out_name, out_directory)
    innards.build_latex(out_directory / out_name, out_directory)

    if remove_artifacts:
        innards.tidy_up_latex_artifacts(out_name, out_directory)
