import logging
from pathlib import Path
import sys

# Add the package to the path before importing.
# (this basically means 2 things: this script is made to be run directly, and you need to have the package installed to
# use it "properly".)
sys.path.append(str(Path(__file__).parents[2]))

from manuscript_generator_3000.importers import markdown_index_file_importer
from manuscript_generator_3000.exporters import markdown_exporter
from manuscript_generator_3000.exporters import latex_pdf_exporter
from manuscript_generator_3000.exporters import epub_exporter
from manuscript_generator_3000.word_count import word_count


def compile():
    logging.basicConfig(level=logging.INFO)

    package_path = Path(__file__).parents[1]
    example_path = Path(__file__).parent.resolve()  # Where this example lives.
    output_path = example_path / Path("output")     # Where we want our output artifacts to end up.

    # Importing a manuscript
    # Seeing as we're using an index file, we'll need to provide that and a root folder.
    # The root folder is where the script will look to find the files included in the index file.
    index_file = example_path / Path("The Unimaginative Software Engineer.md")
    root_folder = example_path
    manuscript = markdown_index_file_importer.load_manuscript_from_index_file(index_file,
                                                                              root_folder)

    # Word count
    # Once we hold a Manuscript object, we can do all sorts of things with it. For starters, we'll print out a word
    # count.
    word_count.log_word_count(manuscript)

    # PDF export (via markdown -> pandoc -> LaTeX)
    # We can export our manuscript into a PDF (which is what I usually do to mark for edits.)
    # To do that, we need to define a few more params.
    # This LaTeX file will contain the output of pandoc converting the markdown output into the latex template, and the
    # params below are substitutions to make in the template (where illustrations live, etc.)
    latex_file = "output.tex"
    illustrations_folder = root_folder  # No illustrations in this example, we could just not pass this in.
    latex_template = package_path / Path("exporters/template.tex")
    babel_language = "english"

    latex_pdf_exporter.export(manuscript,
                              latex_template,
                              illustrations_folder,
                              output_path,
                              latex_file,
                              babel_language,
                              True)

    # EPUB export (via pandoc)
    epub_file = output_path / "output.epub"
    epub_exporter.export(manuscript,
                         illustrations_folder,
                         epub_file)

    # We can also export to markdown, which essentially means we've just concatenated our entire manuscript into a
    # single file. I find this useful as an intermediate format to export into other things (pandoc is awesome) or to
    # have a broader overview of the manuscript.
    out_md_file = output_path / Path("output.md")
    markdown_exporter.export(manuscript, out_md_file)


if __name__ == "__main__":
    compile()
