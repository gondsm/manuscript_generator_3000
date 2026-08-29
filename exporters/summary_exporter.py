from pathlib import Path
from typing import Iterable, List

from ..manuscript import Manuscript
from ..word_count.word_count import count_words_in_manuscript


def _format_chapter_header(chapter: Manuscript.ChapterContribution) -> str:
    """Builds the heading for a chapter, which may or may not have a title of its own.
    """
    # Chapters are numbered within their part, and the numbering here is the one a reader would use.
    name = f"Chapter {chapter.chapter_index + 1}"
    if chapter.chapter_title:
        name = f"{name}: {chapter.chapter_title}"

    return f"### {name} -- {chapter.word_count:,} words"


def _format_chapter(chapter: Manuscript.ChapterContribution) -> List[str]:
    """Renders one chapter, i.e. its heading (if it has one) and the files that make it up.
    """
    lines = []

    # Content that lives outside of any chapter (a short story, say) gets no heading, just its files.
    if chapter.chapter_index >= 0:
        lines.append(_format_chapter_header(chapter))
        lines.append("")

    if not chapter.files:
        lines.append("* (no files yet)")
    else:
        for file in chapter.files:
            lines.append(f"* {file.path.stem} -- {file.word_count:,} words")

    lines.append("")

    return lines


def _group_by_part(composition: Iterable[Manuscript.ChapterContribution]) -> List[List[Manuscript.ChapterContribution]]:
    """Groups chapters into the parts they belong to, keeping the order they appear in.
    """
    groups = []
    for chapter in composition:
        if groups and groups[-1][0].part_index == chapter.part_index:
            groups[-1].append(chapter)
        else:
            groups.append([chapter])

    return groups


def _format_part(chapters: List[Manuscript.ChapterContribution]) -> List[str]:
    """Renders one part, i.e. its heading (if it has one) and all of its chapters.
    """
    lines = []

    # Manuscripts without parts (or content that comes before the first part) get no heading.
    part = chapters[0]
    if part.part_index >= 0:
        part_name = part.part_title if part.part_title else f"Part {part.part_index + 1}"
        part_word_count = sum(chapter.word_count for chapter in chapters)
        lines.append(f"## {part_name} -- {part_word_count:,} words")
        lines.append("")

    for chapter in chapters:
        lines.extend(_format_chapter(chapter))

    return lines


def export(manuscript: Manuscript, out_file: Path) -> None:
    """Writes a summary of how the given Manuscript was put together into the given out_file.

    The summary lists the files that make up each chapter, along with the word count of every chapter and of every
    file, which makes it possible to tell at a glance where the words of a manuscript live.
    """
    lines = [
        f"# Generation summary: {manuscript.config.title}",
        "",
        f"* Generated: {manuscript.config.time.strftime('%Y-%m-%d %H:%M') if manuscript.config.time else 'unknown'}",
        f"* Author: {manuscript.config.author}",
        f"* Word count: {count_words_in_manuscript(manuscript):,}",
        f"* Files: {sum(len(chapter.files) for chapter in manuscript.composition)}",
        f"* Chapters: {sum(1 for chapter in manuscript.composition if chapter.chapter_index >= 0)}",
        "",
    ]

    if not manuscript.composition:
        # Not every importer knows which files a manuscript came from, and that is fine.
        lines.append("This manuscript carries no information about the files it was built from.")
        lines.append("")
    else:
        for chapters in _group_by_part(manuscript.composition):
            lines.extend(_format_part(chapters))

    with open(out_file, "w", encoding="utf-8") as output_file:
        output_file.write("\n".join(lines))
