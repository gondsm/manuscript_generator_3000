import unittest
import tempfile
from typing import List
from pathlib import Path

# We need to start by adding the packages we're testing into the path, which is an unfortunate reality of not wanting to
# install the package just to run unit tests.
import test_utils
test_utils.finagle_dependencies()

from manuscript_generator_3000.importers import markdown_importer_innards as innards
from manuscript_generator_3000.manuscript import Manuscript


class TestExtractInlineConfig(unittest.TestCase):
    def test_no_config(self):
        """No config should be returned if there's no config.
        """
        # There's a break in this line, but no config
        line = "-- Chapter: this is some stuff I added"
        output = innards._extract_inline_config(line)

        self.assertTrue(isinstance(output, dict))
        self.assertEqual(len(output), 0)

    def test_single_config(self):
        """Pull out a single config element.
        """
        line = "-- Chapter -- Title: This is a chapter title"
        output = innards._extract_inline_config(line)

        self.assertTrue(isinstance(output, dict))
        self.assertEqual(len(output), 1)
        self.assertEqual(output["Title"], "This is a chapter title")

    def test_multiple_config(self):
        """Pull out various config elements.
        """
        line = "-- Chapter -- Title: This is a chapter title -- Numbered: False"
        output = innards._extract_inline_config(line)

        self.assertTrue(isinstance(output, dict))
        self.assertEqual(len(output), 2)
        self.assertEqual(output["Title"], "This is a chapter title")
        self.assertEqual(output["Numbered"], "False")

    def test_multiple_config_with_irrelevant_text(self):
        """The function should be robust to some variation around the separator (in case I feel frisky).
        """
        line = "-- Chapter: This is some irrelevant text -- Title: This is a chapter title -- Numbered: False"
        output = innards._extract_inline_config(line)

        self.assertTrue(isinstance(output, dict))
        self.assertEqual(output["Title"], "This is a chapter title")
        self.assertEqual(output["Numbered"], "False")
        self.assertEqual(len(output), 2)


class TestConvertInlineConfigToSeparatorConfig(unittest.TestCase):
    def test_empty_dict(self):
        """Passing in an empty dictionary should return the default config for separators.
        """
        output = innards._convert_inline_config_to_separator_config({})

        # Given an empty dict, we should have an instance of SeparatorConfig that is initialised with the default but IS
        # NOT the same instance as the default.
        self.assertTrue(isinstance(output, Manuscript.SeparatorConfig))
        self.assertEqual(output, innards.SEPARATOR_CONFIG_DEFAULT)
        self.assertFalse(output is innards.SEPARATOR_CONFIG_DEFAULT)

    def test_nonsensical_dict(self):
        """Passing in a dict with weird keys should behave the same as an empty dict.
        """
        input = {"sOmE_wEiRd_kEy": "sOmE_wEiRd_vAlUe"}
        output = innards._convert_inline_config_to_separator_config(input)

        self.assertTrue(isinstance(output, Manuscript.SeparatorConfig))
        self.assertEqual(output, innards.SEPARATOR_CONFIG_DEFAULT)
        self.assertFalse(output is innards.SEPARATOR_CONFIG_DEFAULT)

    def test_title(self):
        """Gief title, get title
        """
        input = {"Title": "This is a chapter title"}
        output = innards._convert_inline_config_to_separator_config(input)

        self.assertTrue(isinstance(output, Manuscript.SeparatorConfig))
        self.assertEqual(output.title, "This is a chapter title")
        self.assertEqual(output.numbered, True)

    def test_title_and_numbered(self):
        """Gief title, get title
        """
        input = {"Title": "This is a chapter title", "Numbered": "False"}
        output = innards._convert_inline_config_to_separator_config(input)

        self.assertTrue(isinstance(output, Manuscript.SeparatorConfig))
        self.assertEqual(output.title, "This is a chapter title")
        self.assertEqual(output.numbered, False)


class TestReplaceIndicators(unittest.TestCase):
    def test_chapter_no_properties(self):
        """We should get an empty StartChapter if no properties are in the lines
        """
        lines = [
            "This is the first line",
            "-- Chapter",
            "This is the second line"
        ]

        output = innards.replace_indicators(lines)

        self.assertEqual(output[0], lines[0])
        self.assertIsInstance(output[1], Manuscript.StartChapter)
        self.assertEqual(output[2], lines[2])

        self.assertEqual(output[1].config, innards.SEPARATOR_CONFIG_DEFAULT)

    def test_chapter_with_properties(self):
        """We should get an empty StartChapter if no properties are in the lines
        """
        lines = [
            "This is the first line",
            "-- Chapter: This is some irrelevant text -- Title: This is a chapter title -- Numbered: False",
            "This is the second line"
        ]

        output = innards.replace_indicators(lines)

        self.assertEqual(output[0], lines[0])
        self.assertIsInstance(output[1], Manuscript.StartChapter)
        self.assertEqual(output[2], lines[2])

        self.assertNotEqual(output[1].config, innards.SEPARATOR_CONFIG_DEFAULT)
        self.assertEqual(output[1].config.title, "This is a chapter title")
        self.assertEqual(output[1].config.numbered, False)

    def test_part_no_properties(self):
        """We should get an empty StartPart if no properties are in the lines
        """
        lines = [
            "This is the first line",
            "-- Part",
            "This is the second line"
        ]

        output = innards.replace_indicators(lines)

        self.assertEqual(output[0], lines[0])
        self.assertIsInstance(output[1], Manuscript.StartPart)
        self.assertEqual(output[2], lines[2])

        self.assertEqual(output[1].config, innards.SEPARATOR_CONFIG_DEFAULT)

    def test_part_with_properties(self):
        """We should get an empty StartChapter if no properties are in the lines
        """
        lines = [
            "This is the first line",
            "-- Part: This is some irrelevant text -- Title: This is a part title -- Numbered: False",
            "This is the second line"
        ]

        output = innards.replace_indicators(lines)

        self.assertEqual(output[0], lines[0])
        self.assertIsInstance(output[1], Manuscript.StartPart)
        self.assertEqual(output[2], lines[2])

        self.assertNotEqual(output[1].config, innards.SEPARATOR_CONFIG_DEFAULT)
        self.assertEqual(output[1].config.title, "This is a part title")
        self.assertEqual(output[1].config.numbered, False)

    def test_scene(self):
        """We should get an empty StartPart if no properties are in the lines
        """
        lines = [
            "This is the first line",
            "---",
            "This is the second line"
        ]

        output = innards.replace_indicators(lines)

        self.assertEqual(output[0], lines[0])
        self.assertIsInstance(output[1], Manuscript.BreakScene)
        self.assertEqual(output[2], lines[2])


class TestExtractRelevantLinesFromIndexFile(unittest.TestCase):
    TEST_FILE_NAME = Path("test_file")

    def write_content_to_test_file(self, content: List[str]):
        """Writes content to the test file we know about.
        """
        with open(self.TEST_FILE_NAME, "w") as test_file:
            for line in content:
                test_file.write(line)
                test_file.write("\n")

    def remove_test_file(self):
        self.TEST_FILE_NAME.unlink()

    def tearDown(self) -> None:
        super().tearDown()
        self.remove_test_file()

    def test_no_relevant_lines(self):
        """If there are no relevant lines, we shouldn't get anything back.
        """
        # Define and write out some pointless content
        content = [
            "This is an irrelevant line",
            "This is another irrelevant line",
            "All good things come in threes."
        ]

        self.write_content_to_test_file(content)

        # Call the function we're testing
        relevant_lines = innards.extract_relevant_lines_from_index_file(self.TEST_FILE_NAME, innards.DelimiterMode.TASK)

        # We shouldn't have anything
        self.assertEqual(relevant_lines, [])

    def test_one_relevant_line(self):
        """If there's only one relevant line, we should see it.
        """
        # Define and write out some pointful content
        content = [
            "This is an irrelevant line",
            "This is another irrelevant line",
            "All good things come in threes.",
            "- [ ] [[ this is a relevant line because it (potentially) contains a file to include"
        ]

        self.write_content_to_test_file(content)

        # Call the function we're testing
        relevant_lines = innards.extract_relevant_lines_from_index_file(self.TEST_FILE_NAME, innards.DelimiterMode.TASK)

        # We should have the one relevant line
        self.assertEqual(len(relevant_lines), 1)
        self.assertEqual(relevant_lines, [content[-1]])

    def test_one_relevant_line_other_list(self):
        """If there's only one relevant line, we should see it.
        """
        # Define and write out some pointful content
        relevant_line = "- [ ] [[ this is a relevant line because it (potentially) contains a file to include"
        content = [
            "This is an irrelevant line",
            "This is another irrelevant line",
            "All good things come in threes.",
            relevant_line,
            "- This is another list element that is not relevant",
            "- And another",
        ]

        self.write_content_to_test_file(content)

        # Call the function we're testing
        relevant_lines = innards.extract_relevant_lines_from_index_file(self.TEST_FILE_NAME, innards.DelimiterMode.TASK)

        # We should have the one relevant line
        self.assertEqual(len(relevant_lines), 1)
        self.assertEqual(relevant_lines, [relevant_line])

    def test_two_relevant_lines(self):
        # Define and write out some even more pointful content
        relevant_lines = [
            "- [ ] [[ this is a relevant line because it (potentially) contains a file to include",
            "- [ ] [[ this is another relevant line",
        ]
        content = [
            "This is an irrelevant line",
            "This is another irrelevant line",
            "All good things come in threes.",
            relevant_lines[0],
            relevant_lines[1],
            "- This is another list element that is not relevant",
            "- And another",
        ]

        self.write_content_to_test_file(content)

        # Call the function we're testing
        relevant_lines = innards.extract_relevant_lines_from_index_file(self.TEST_FILE_NAME, innards.DelimiterMode.TASK)

        # We should have the one relevant line
        self.assertEqual(len(relevant_lines), 2)
        self.assertEqual(relevant_lines, relevant_lines)


class TestExtractRelevantLinesFromIndexFileEmojiMode(unittest.TestCase):
    """ Same tests as above but using the SHORT DelimiterMode.

    (I prefer duplicating the tests and later remove the deprecated version than try to be clever about writing tests
    around config.)
    """
    TEST_FILE_NAME = Path("test_file")

    def write_content_to_test_file(self, content: List[str]):
        """Writes content to the test file we know about.
        """
        with open(self.TEST_FILE_NAME, "w", encoding="utf-8") as test_file:
            for line in content:
                test_file.write(line)
                test_file.write("\n")

    def remove_test_file(self):
        self.TEST_FILE_NAME.unlink()

    def tearDown(self) -> None:
        super().tearDown()
        self.remove_test_file()

    def test_no_relevant_lines(self):
        """If there are no relevant lines, we shouldn't get anything back.
        """
        # Define and write out some pointless content
        content = [
            "This is an irrelevant line",
            "This is another irrelevant line",
            "All good things come in threes."
        ]

        self.write_content_to_test_file(content)

        # Call the function we're testing
        relevant_lines = innards.extract_relevant_lines_from_index_file(self.TEST_FILE_NAME,
                                                                        innards.DelimiterMode.EMOJI)

        # We shouldn't have anything
        self.assertEqual(relevant_lines, [])

    def test_one_relevant_line(self):
        """If there's only one relevant line, we should see it.
        """
        # Define and write out some pointful content
        content = [
            "This is an irrelevant line",
            "This is another irrelevant line",
            "All good things come in threes.",
            "- 📚 [[ this is a relevant line because it (potentially) contains a file to include"
        ]

        self.write_content_to_test_file(content)

        # Call the function we're testing
        relevant_lines = innards.extract_relevant_lines_from_index_file(self.TEST_FILE_NAME,
                                                                        innards.DelimiterMode.EMOJI)

        # We should have the one relevant line
        self.assertEqual(len(relevant_lines), 1)
        self.assertEqual(relevant_lines, [content[-1]])

    def test_one_relevant_line_other_list(self):
        """If there's only one relevant line, we should see it.
        """
        # Define and write out some pointful content
        relevant_line = "- 📚 [[ this is a relevant line because it (potentially) contains a file to include"
        content = [
            "This is an irrelevant line",
            "This is another irrelevant line",
            "All good things come in threes.",
            relevant_line,
            "- This is another list element that is not relevant",
            "- And another",
        ]

        self.write_content_to_test_file(content)

        # Call the function we're testing
        relevant_lines = innards.extract_relevant_lines_from_index_file(self.TEST_FILE_NAME,
                                                                        innards.DelimiterMode.EMOJI)

        # We should have the one relevant line
        self.assertEqual(len(relevant_lines), 1)
        self.assertEqual(relevant_lines, [relevant_line])

    def test_two_relevant_lines(self):
        # Define and write out some even more pointful content
        relevant_lines = [
            "- 📚 [[ this is a relevant line because it (potentially) contains a file to include",
            "- 📚 [[ this is another relevant line",
        ]
        content = [
            "This is an irrelevant line",
            "This is another irrelevant line",
            "All good things come in threes.",
            relevant_lines[0],
            relevant_lines[1],
            "- This is another list element that is not relevant",
            "- And another",
        ]

        self.write_content_to_test_file(content)

        # Call the function we're testing
        relevant_lines = innards.extract_relevant_lines_from_index_file(self.TEST_FILE_NAME,
                                                                        innards.DelimiterMode.EMOJI)

        # We should have the one relevant line
        self.assertEqual(len(relevant_lines), 2)
        self.assertEqual(relevant_lines, relevant_lines)


class TestFindMarkdownFilePath(unittest.TestCase):
    """Tests for resolving a wikilink reference to a single markdown file on disk.
    """

    def setUp(self) -> None:
        super().setUp()
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.root_folder = Path(self._tmp_dir.name)

    def tearDown(self) -> None:
        super().tearDown()
        self._tmp_dir.cleanup()

    def _touch(self, relative_path: str) -> Path:
        """Creates an (empty) markdown file at the given path relative to the root folder.
        """
        full_path = self.root_folder / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text("", encoding="utf-8")
        return full_path

    def test_single_match(self):
        """A reference that maps to exactly one file should resolve to that file.
        """
        expected = self._touch("Text/010 - Example.md")

        output = innards._find_markdown_file_path(Path("010 - Example"), self.root_folder)

        self.assertEqual(output, expected)

    def test_substring_is_not_a_match(self):
        """A reference must match on the exact file stem, not on a substring.
        """
        expected = self._touch("Text/010 - Example.md")
        # This companion file contains the reference as a substring but has a different stem.
        self._touch("Zettelkasten/010 - Example - ZK Links.md")

        output = innards._find_markdown_file_path(Path("010 - Example"), self.root_folder)

        self.assertEqual(output, expected)

    def test_no_match_raises(self):
        """A reference that matches no file should raise, naming the missing reference.
        """
        self._touch("Text/010 - Example.md")

        with self.assertRaises(ValueError) as context:
            innards._find_markdown_file_path(Path("999 - Does Not Exist"), self.root_folder)

        self.assertIn("999 - Does Not Exist", str(context.exception))

    def test_ambiguous_match_raises(self):
        """A reference whose exact stem exists in two folders should raise, listing both files.
        """
        first = self._touch("Text/010 - Example.md")
        second = self._touch("Backup/010 - Example.md")

        with self.assertRaises(ValueError) as context:
            innards._find_markdown_file_path(Path("010 - Example"), self.root_folder)

        message = str(context.exception)
        self.assertIn("010 - Example", message)
        self.assertIn(str(first), message)
        self.assertIn(str(second), message)


if __name__ == '__main__':
    unittest.main()
