import unittest

# We need to start by adding the packages we're testing into the path, which is an unfortunate reality of not wanting to
# install the package just to run unit tests.
import test_utils
test_utils.finagle_dependencies()

from manuscript_generator_3000.manuscript import Manuscript
from manuscript_generator_3000.importers import markdown_importer_innards

class TestManuscript(unittest.TestCase):
    def test_construction(self):
        """It should be possible to construct a Manuscript without anything blowing up.
        """
        sample_content = []
        sample_config = Manuscript.Config(title="title",
                                          author="author",
                                          cover="cover",
                                          time = None)
        sample_manuscript = Manuscript(sample_content, sample_config)


class TestIsControlType(unittest.TestCase):
    def test_chapter(self):
        """Test whether a chapter start is flagged as a control element
        """
        lines = [
            "text",
            Manuscript.StartChapter(markdown_importer_innards.SEPARATOR_CONFIG_DEFAULT),
            "more text"
        ]

        self.assertFalse(Manuscript.is_control_type(lines[0]))
        self.assertTrue(Manuscript.is_control_type(lines[1]))
        self.assertFalse(Manuscript.is_control_type(lines[2]))


if __name__ == '__main__':
    unittest.main()
