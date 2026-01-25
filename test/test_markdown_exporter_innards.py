import unittest

# We need to start by adding the packages we're testing into the path, which is an unfortunate reality of not wanting to
# install the package just to run unit tests.
import test_utils
test_utils.finagle_dependencies()

from manuscript_generator_3000.exporters import markdown_exporter_innards as innards
from manuscript_generator_3000.manuscript import Manuscript


class TestConvertContentToLines(unittest.TestCase):
    def test_chapter_break(self):
        """Content that includes a chapter break should be converted appropriately
        """
        separator_config = Manuscript.SeparatorConfig("Test Title", False)
        start_chapter = Manuscript.StartChapter(separator_config)

        content = [
            "text",
            start_chapter,
            "more text"
        ]

        cfg = Manuscript.Config(
            title="title",
            author="author",
            cover="cover",
            time=None,
            scene_separator_type="normal",
        )

        m = Manuscript(content, cfg)

        output = innards.convert_content_to_lines(m)

        self.assertEqual(len(output), 3)
        self.assertEqual(output[1], "## Test Title {.unnumbered}")


if __name__ == '__main__':
    unittest.main()
