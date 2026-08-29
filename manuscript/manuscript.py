# Using a nested class below to define a type in another nested class
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, field
import datetime
from typing import List, Union

@dataclass
class Manuscript:
    """A class that holds an entire manuscript.

    A manuscript can be a novel, a short story, a novella, or whatever other format that can be defined in terms of

    * Parts, which contain
    * Chapters, which contain
    * Scenes.

    Internally, this class maintains an iterable that contains the full text, with separator elements for parts, etc,
    introduced in the midst of those elements, something to the tune of

    [
        StartChapter,
        "Everyone knows _any_ good novel starts with a prologue.",
        StartPart,
        StartChapter,
        "This is the first block of text which is also the first chapter.",
        StartChapter,
        "This is the second chapter.",
        BreakScene,
        "Plot twist, this chapter has two scenes! Exciting!"
    ]

    and so on. These elements can contain properties. See below.

    There is no requirement for a manuscript to contain all three, i.e. a short story would not traditionally be broken
    into parts or chapters, but it could be broken into scenes.

    The content of the manuscript can contain markdown formatting (**bold**, _italics_, etc) and the exporters should be
    able to deal with that.
    """

    @dataclass
    class Config:
        """Holds the entire configuration of a manuscript
        """
        title: str
        author: str
        cover: Path
        time: datetime.datetime
        # This controls the rendering type for scene separators.
        # "normal" should yield visible scene separators, "blank" should yield invisible separators, and "none" should
        # do what it says on the tin.
        # TODO: should this be another enum?
        scene_separator_type: str

    @dataclass
    class SeparatorConfig:
        """Holds the configuration of a separator, e.g. a chapter separator.
        """
        title: str
        numbered: bool

    @dataclass
    class StartPart:
        """Signals the start of a new part.
        """
        config: Manuscript.SeparatorConfig

    @dataclass
    class StartChapter:
        """Signals the start of a part.
        """
        config: Manuscript.SeparatorConfig

    @dataclass
    class BreakScene:
        """Signals the start of a scene.
        (And scenes don't have attributes)
        """
        pass

    @dataclass
    class FileContribution:
        """A single source file that contributed text to a manuscript.
        """
        path: Path
        word_count: int

    @dataclass
    class ChapterContribution:
        """The source files that make up one chapter, in the order in which they appear.

        A chapter can be made up of any number of files (including none at all, for a chapter that has been declared
        but not yet written).

        Indices are zero-based and count within their container, i.e. chapter_index counts chapters within a part.
        Both are negative for content that lives outside of any part/chapter, which is possible for manuscripts that
        do not use those separators at all (a short story, say).
        """
        part_index: int
        part_title: str
        chapter_index: int
        chapter_title: str
        files: List[Manuscript.FileContribution] = field(default_factory=list)

        @property
        def word_count(self) -> int:
            return sum(file.word_count for file in self.files)

    @classmethod
    def is_control_type(cls, input) -> bool:
        """Returns whether the given string is one of the control strings this class knows about.
        """
        # TODO: would be cool to not have to repeat all of these names here, which is where preprocessor macros would
        # come in handy.
        control_types = [cls.StartPart, cls.StartChapter, cls.BreakScene]
        return any([isinstance(input, elem) for elem in control_types])

    # The contents of the Manuscript will be a list of strings with the actual text, interspersed with the separator
    # classes defined above.
    Content = List[Union[str, StartPart, StartChapter, BreakScene]]

    # Lastly, the things that this actually contains.
    content: Content
    config: Config
    original_files: List[Path] = field(default_factory=list)
    # Describes which files made up which chapter, and how much each of them contributed. Importers that have no notion
    # of source files (or of chapters) can leave this empty.
    composition: List[ChapterContribution] = field(default_factory=list)

    def split_into_parts(self) -> List["Manuscript"]:
        """Split this Manuscript into per-Part Manuscript objects.

        Returns a list of Manuscript objects corresponding to each `StartPart` block
        found in `self.content`. Each part's `config.title` is set to
        "<original title> - <part title>" when a title is present on the separator.
        """
        parts: List[Manuscript] = []

        content = self.content

        # Find indices of part separators
        part_indices = [i for i, elem in enumerate(content) if isinstance(elem, Manuscript.StartPart)]

        for idx_i, start_idx in enumerate(part_indices):
            end_idx = part_indices[idx_i + 1] if idx_i + 1 < len(part_indices) else len(content)
            part_content = content[start_idx:end_idx]

            # Determine title from the StartPart separator if available
            part_title = None
            first_elem = part_content[0] if part_content else None
            if isinstance(first_elem, Manuscript.StartPart):
                part_title = first_elem.config.title

            # Create a new Config for the part manuscript, prefixing the original title
            # with the part title when present.
            original_cfg = self.config
            if part_title:
                title = f"{original_cfg.title} - {part_title}"
            else:
                title = original_cfg.title

            part_config = Manuscript.Config(title,
                                            original_cfg.author,
                                            original_cfg.cover,
                                            original_cfg.time,
                                            original_cfg.scene_separator_type)

            # The composition is already broken down by part, so we can just hand each part the entries that belong
            # to it.
            part_composition = [entry for entry in self.composition if entry.part_index == idx_i]

            # TODO: Part manuscripts won't have original files for now, we'd need to fish them out or hold them differently.
            part_manuscript = Manuscript(part_content, part_config, None, part_composition)
            parts.append(part_manuscript)

        return parts
