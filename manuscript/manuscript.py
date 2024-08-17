# Using a nested class below to define a type in another nested class
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
import datetime
from collections.abc import Iterable


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

    @classmethod
    def is_control_type(cls, input) -> bool:
        """Returns whether the given string is one of the control strings this class knows about.
        """
        # TODO: would be cool to not have to repeat all of these names here, which is where preprocessor macros would
        # come in handy.
        control_types = [cls.StartPart, cls.StartChapter, cls.BreakScene]
        return any([isinstance(input, elem) for elem in control_types])

    # Lastly, the things that this actually contains.
    content: Iterable[str]
    config: Config
