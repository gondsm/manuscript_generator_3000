"""
Manuscript Generation Script

This script discovers and generates manuscripts from Markdown files.

DISCOVERY:
- Index files: Files named "* - Index File.md" or with front matter property "type: index_file"
- Short fiction: Files with front matter property "type: short_fiction"

PROPERTY VALUES:
- type: "index_file" for multi-part manuscripts or "short_fiction" for single-file stories
- manuscript_series: (optional) Groups manuscripts in the same series

PROCESSING:
1. Discovers all eligible manuscript files in the root directory
2. Generates PDF and EPUB for each manuscript in parallel
3. Creates individual files for each part (for multi-part manuscripts)
4. Writes a generation summary next to each manuscript, listing the files that make up each chapter and their word
   counts
5. Outputs a summary with word counts and file locations
6. Saves generation logs and summary to output directory
"""

import argparse
import concurrent.futures
import datetime
import logging
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent / Path("../../src")))

# Importers
from manuscript_generator_3000.importers import markdown_index_file_importer
from manuscript_generator_3000.importers import markdown_single_file_importer

# Exporters
from manuscript_generator_3000.exporters import epub_exporter
from manuscript_generator_3000.exporters import latex_pdf_exporter
from manuscript_generator_3000.exporters import markdown_exporter
from manuscript_generator_3000.exporters import summary_exporter
from manuscript_generator_3000.exporters import zip_exporter

# Utilities
from manuscript_generator_3000.word_count.word_count import count_words_in_manuscript
from manuscript_generator_3000.importers.markdown_importer_innards import extract_properties
from manuscript_generator_3000.discoverers.manuscript_file_discoverer import discover_manuscript_files
from manuscript_generator_3000.discoverers.cover_directory_discoverer import find_cover_directory

# Pull in the whole package just to use its path
import manuscript_generator_3000 as _generator_pkg

TEMPLATE_PATH = Path(_generator_pkg.__file__).resolve().parent / "exporters" / "template.tex"
SERIES_PROPERTY_NAME = "manuscript_series"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover manuscript files and export them to PDF, EPUB, ZIP, etc."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Root folder to search for manuscript files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(_generator_pkg.__file__).resolve().parent / "latex",
        help="Directory where PDF/EPUB outputs will be written.",
    )
    parser.add_argument(
        "--filter",
        default="",
        help="Only generate manuscripts whose index file name contains this string (case-insensitive).",
    )
    return parser.parse_args()


def call_manuscript_exporters(manuscript, illustrations_folder: Path, manuscript_output_dir: Path, output_name: str, epub_name: str, markdown_name: str, zip_name: str, summary_name: str) -> None:
    """Export a manuscript to PDF, EPUB, Markdown, original source files as ZIP, and a generation summary."""
    latex_pdf_exporter.export(
        manuscript,
        TEMPLATE_PATH,
        illustrations_folder,
        manuscript_output_dir,
        output_name,
        "portuguese",
        True,
    )

    epub_exporter.export(
        manuscript,
        illustrations_folder,
        manuscript_output_dir / epub_name,
    )

    markdown_exporter.export(
        manuscript,
        manuscript_output_dir / markdown_name,
    )

    zip_exporter.export(manuscript, manuscript_output_dir / zip_name)

    summary_exporter.export(manuscript, manuscript_output_dir / summary_name)


def export_manuscript(file_path: Path, root_folder: Path, output_dir: Path, manuscript_type: str) -> dict:
    """Export a manuscript and return summary data."""
    # Extract series from properties first to determine output directory
    # TODO: We shouldn't need to do this here. The importer should write series to the Manuscript object, and then we just use that.
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    _, properties = extract_properties(lines)
    series = properties.get(SERIES_PROPERTY_NAME, "").strip()
    
    # Determine output directory structure based on type
    if manuscript_type == "short_fiction":
        manuscript_output_dir = output_dir / series / "Short Fiction" / file_path.stem if series else output_dir / file_path.stem
    else:
        manuscript_output_dir = output_dir / series / file_path.stem if series else output_dir / file_path.stem
    
    manuscript_output_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = manuscript_output_dir / "generation.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_file)]
    )

    logging.info("Generating %s for %s", manuscript_type, file_path)

    output_name = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d") + " - " + file_path.stem + ".tex"
    epub_name = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d") + " - " + file_path.stem + ".epub"
    markdown_name = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d") + " - " + file_path.stem + ".md"
    zip_name = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d") + " - " + file_path.stem + " - original_files.zip"
    summary_name = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d") + " - " + file_path.stem + " - generation_summary.md"

    # Load manuscript based on type
    if manuscript_type == "short_fiction":
        manuscript = markdown_single_file_importer.load_manuscript_from_file(file_path.name, root_folder)
    else:  # index
        manuscript = markdown_index_file_importer.load_manuscript_from_index_file(
            file_path,
            root_folder,
            markdown_index_file_importer.DelimiterMode.EMOJI,
        )
    
    if not manuscript:
        logging.error("Failed to load %s: %s", manuscript_type, file_path)
        return None

    # TODO: this functionality should be in the main package, and be very optional.
    # TODO: have a think: how is global config supposed to interact with properties? Are they redundant? Should we just have properties?
    illustrations_folder = find_cover_directory(root_folder, manuscript.config.cover)

    manuscript_wc = count_words_in_manuscript(manuscript)

    # Export main manuscript (including original files as zip)
    with open(log_file, 'w', encoding='utf-8') as log_f:
        with redirect_stdout(log_f), redirect_stderr(log_f):
            call_manuscript_exporters(
                manuscript,
                illustrations_folder,
                manuscript_output_dir,
                output_name,
                epub_name,
                markdown_name,
                zip_name,
                summary_name,
            )

    parts_data = []
    
    for part in manuscript.split_into_parts():
        part_slug = part.config.title.replace(" ", "_")
        part_tex_name = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d") + " - " + part_slug + ".tex"
        part_epub_name = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d") + " - " + part_slug + ".epub"
        part_markdown_name = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d") + " - " + part_slug + ".md"
        part_zip_name = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d") + " - " + part_slug + " - original_files.zip"
        part_summary_name = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d") + " - " + part_slug + " - generation_summary.md"

        part_wc = count_words_in_manuscript(part)
        parts_data.append({
            "title": part.config.title,
            "word_count": part_wc,
        })

        with open(log_file, 'a', encoding='utf-8') as log_f:
            with redirect_stdout(log_f), redirect_stderr(log_f):
                call_manuscript_exporters(
                    part,
                    illustrations_folder,
                    manuscript_output_dir,
                    part_tex_name,
                    part_epub_name,
                    part_markdown_name,
                    part_zip_name,
                    part_summary_name,
                )

    return {
        "index_file": file_path,
        "output_path": manuscript_output_dir,
        "summary_file": manuscript_output_dir / summary_name,
        "word_count": manuscript_wc,
        "parts": parts_data,
        "type": manuscript_type,
    }


def compile_summary(summaries: list) -> str:
    """Compile generation summary from summaries into a formatted string."""
    summary_lines = []
    summary_lines.append("\n" + "=" * 80)
    summary_lines.append("GENERATION SUMMARY")
    summary_lines.append("=" * 80)
    
    total_manuscripts = len(summaries)
    total_words = sum(summary["word_count"] for summary in summaries)
    
    # Calculate totals by type
    index_summaries = [s for s in summaries if s["type"] == "index"]
    short_fiction_summaries = [s for s in summaries if s["type"] == "short_fiction"]
    
    index_total_manuscripts = len(index_summaries)
    index_total_words = sum(s["word_count"] for s in index_summaries)
    
    short_fiction_total_manuscripts = len(short_fiction_summaries)
    short_fiction_total_words = sum(s["word_count"] for s in short_fiction_summaries)
    
    for summary in summaries:
        index_stem = summary["index_file"].stem
        summary_lines.append(f"\n{index_stem}")
        summary_lines.append(f"  * Index file: {summary['index_file']}")
        summary_lines.append(f"  * Output: {summary['output_path']}")
        summary_lines.append(f"  * Generation summary: {summary['summary_file'].name}")
        summary_lines.append(f"  * Word count: {summary['word_count']:,}")
        
        if summary["parts"]:
            summary_lines.append(f"  * Parts:")
            for part in summary["parts"]:
                summary_lines.append(f"    * {part['title']}: {part['word_count']:,} words")
    
    summary_lines.append("\n")
    summary_lines.append("TOTALS")
    summary_lines.append(f"  * Total manuscripts: {total_manuscripts}")
    summary_lines.append(f"  * Total word count: {total_words:,}")
    summary_lines.append(f"  * Index files: {index_total_manuscripts} manuscripts, {index_total_words:,} words")
    summary_lines.append(f"  * Short fiction: {short_fiction_total_manuscripts} manuscripts, {short_fiction_total_words:,} words")
    summary_lines.append("=" * 80)
    
    return "\n".join(summary_lines)


def generate_manuscripts(manuscript_files: list[tuple[Path, str]], root_folder: Path, output_dir: Path) -> list[dict]:
    """Generate manuscripts in parallel and return summary metadata."""
    summaries = []
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # Prepare arguments for each manuscript
        futures = []
        for manuscript_file, manuscript_type in manuscript_files:
            logging.info("Submitting manuscript for generation: %s (%s)", manuscript_file, manuscript_type)
            future = executor.submit(export_manuscript, manuscript_file, root_folder, output_dir, manuscript_type)
            futures.append((manuscript_file, future))

        # Collect results
        for manuscript_file, future in futures:
            try:
                summary = future.result()
                logging.info("Completed manuscript: %s", manuscript_file)
                if summary:
                    summaries.append(summary)
            except Exception as exc:
                logging.exception("Failed to generate manuscript %s: %s", manuscript_file, exc)

    return summaries


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO)

    root_folder = args.root
    output_dir = args.output_dir

    # Sanitise
    if not root_folder.exists():
        logging.fatal(f"Root folder does not exist: {root_folder}")
        return
    
    if not output_dir.exists():
        logging.fatal(f"Output directory does not exist; creating: {output_dir}")
        return

    # Find manuscript files
    manuscript_files = discover_manuscript_files(root_folder)
    if not manuscript_files:
        logging.fatal("No manuscript files found.")
        return

    # Apply filter
    # (Empty strings are in all strings)
    manuscript_files = [(path, type_) for path, type_ in manuscript_files if args.filter.lower() in path.stem.lower()]
    if not manuscript_files:
        logging.fatal(f"No manuscript files match filter: {args.filter}")
        return

    # Log our findings
    logging.info(f"Discovered {len(manuscript_files)} manuscript(s):")
    for manuscript_file, manuscript_type in manuscript_files:
        logging.info(f"- {manuscript_file} ({manuscript_type})")

    # Generate the manuscripts
    summaries = generate_manuscripts(manuscript_files, root_folder, output_dir)

    # Print summary
    summary_content = compile_summary(summaries)
    logging.info(summary_content)
    summary_file = (output_dir / "generation_summary.txt")
    summary_file.write_text(summary_content)


if __name__ == "__main__":
    main()
