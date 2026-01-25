import unittest

# We need to start by adding the packages we're testing into the path, which is an unfortunate reality of not wanting to
# install the package just to run unit tests.
import test_utils
test_utils.finagle_dependencies()

from manuscript_generator_3000.manuscript import Manuscript
from manuscript_generator_3000.importers import markdown_importer_innards
import datetime

class TestManuscript(unittest.TestCase):
    def test_construction(self):
        """It should be possible to construct a Manuscript without anything blowing up.
        """
        sample_content = []
        sample_config = Manuscript.Config(title="title",
                          author="author",
                          cover="cover",
                          time = None,
                          scene_separator_type="normal")
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


class TestSplitManuscriptIntoParts(unittest.TestCase):
    def test_no_parts_returns_empty_list(self):
        """If there's no parts, we should get an empty list back.
        """
        cfg = Manuscript.Config(
            title="title",
            author="author",
            cover="cover",
            time=None,
            scene_separator_type="normal",
        )
        m = Manuscript(["Line one", "Line two"], cfg)

        parts = m.split_into_parts()

        self.assertIsInstance(parts, list)
        self.assertEqual(len(parts), 0)

    def test_single_part_title_is_prefixed(self):
        """Manuscripts from parts should have the original title prefixed to the part title.
        """
        cfg = Manuscript.Config(
            title="title",
            author="author",
            cover="cover",
            time=None,
            scene_separator_type="normal",
        )
        sep_cfg = Manuscript.SeparatorConfig("Part A", True)
        content = [Manuscript.StartPart(sep_cfg), "Para 1", "Para 2"]
        m = Manuscript(content, cfg)

        parts = m.split_into_parts()

        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0].config.title, "title - Part A")
        self.assertEqual(parts[0].content, content)

    def test_multiple_parts(self):
        """We can have many parts in a manuscript, and they get split correctly.
        """
        cfg = Manuscript.Config(
            title="title",
            author="author",
            cover="cover",
            time=None,
            scene_separator_type="normal",
        )
        sep1 = Manuscript.SeparatorConfig("One", True)
        sep2 = Manuscript.SeparatorConfig("Two", True)

        content = [
            "Intro line",
            Manuscript.StartPart(sep1),
            "P1",
            Manuscript.StartPart(sep2),
            "P2",
        ]
        m = Manuscript(content, cfg)

        parts = m.split_into_parts()

        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0].config.title, "title - One")
        self.assertEqual(parts[1].config.title, "title - Two")
        self.assertEqual(parts[0].content, content[1:3])
        self.assertEqual(parts[1].content, content[3:5])


if __name__ == "__main__":
    unittest.main()
