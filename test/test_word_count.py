import unittest

import test_utils
test_utils.finagle_dependencies()
import word_count
from manuscript import Manuscript


class TestWordCount(unittest.TestCase):
    def test_count_words(self):
        """The word count function should, to the surprise of no one, count words.
        """
        test_string = "This is a string with seven words."
        count = word_count.count_words(test_string)

        self.assertEqual(count, 7)

    def test_count_words_in_manuscript(self):
        """And the interface function should do its sums correctly.
        """
        sample_content = ["This is a string with seven words.",
                          "This is a string with seven words."]

        # We're creating a Manuscript with no config, which should probably be a no-no, but this'll do for the moment.
        sample_manuscript = Manuscript(sample_content, None)

        count = word_count.count_words_in_manuscript(sample_manuscript)
        self.assertEqual(count, 14)


if __name__ == '__main__':
    unittest.main()
