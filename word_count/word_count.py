import logging

from ..manuscript import Manuscript

logger = logging.getLogger(__name__)


def count_words(string: str) -> int:
    """Count the number of words in a given string.

    This is somewhat janky, since it may very well count things that are not words, but when manuscripts are in the many
    thousands of words, does it matter?
    """
    words = string.split()
    return len(words)


def count_words_in_manuscript(manuscript: Manuscript) -> int:
    count = sum([count_words(elem) for elem in manuscript.content if not Manuscript.is_control_string(elem)])
    return count

def log_word_count(manuscript: Manuscript) -> None:
    """Writes word count stats of the Manuscript to the logs.
    """
    logger.info(f"Word count: {count_words_in_manuscript(manuscript)} words.")
