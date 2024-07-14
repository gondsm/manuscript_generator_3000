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
        START_PROLOGUE,
        "Everyone knows _any_ good novel starts with a prologue.",
        START_PART,
        START_CHAPTER,
        "This is the first block of text which is also the first chapter.",
        START_CHAPTER,
        "This is the second chapter.",
        BREAK_SCENE,
        "Plot twist, this chapter has two scenes! Exciting!"
    ]

    and so on.

    There is no requirement for a manuscript to contain all three, i.e. a short story would not traditionally be broken
    into parts or chapters, but it could be broken into scenes.

    The content of the manuscript can contain markdown formatting (**bold**, _italics_, etc) and the exporters should be
    able to deal with that.
    """
    # Each of these signals the start of a new section in the manuscript.
    START_PROLOGUE = "START_PROLOGUE"
    START_PART = "START_PART"
    START_CHAPTER = "START_CHAPTER"

    # Scenes are different as we don't signal their start, only their breaks.
    BREAK_SCENE = "BREAK_SCENE"

    @dataclass
    class Config:
        """Holds the entire configuration of a manuscript
        """
        title: str
        author: str
        cover: Path
        time: datetime.datetime

    @classmethod
    def is_control_string(cls, string: str) -> bool:
        """Returns whether the given string is one of the control strings this class knows about.
        """
        # TODO: would be cool to not have to repeat all of these names here, which is where preprocessor macros would
        # come in handy.
        control_strings = [cls.START_PROLOGUE, cls.START_PART, cls.START_CHAPTER, cls.BREAK_SCENE]
        return any([elem in string for elem in control_strings])

    # Lastly, the things that this actually contains.
    content: Iterable[str]
    config: Config
