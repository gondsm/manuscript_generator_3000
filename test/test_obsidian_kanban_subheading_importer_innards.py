import unittest

# We need to start by adding the packages we're testing into the path, which is an unfortunate reality of not wanting to
# install the package just to run unit tests.
import test_utils
test_utils.finagle_dependencies()

from manuscript_generator_3000.importers import obsidian_kanban_subheading_importer_innards as innards
from manuscript_generator_3000.manuscript import Manuscript


class TestExtractInlineConfig(unittest.TestCase):
    def test_no_config(self):
        """No config should be returned if there's no config.
        """
        # There's a break in this line, but no config
        line = "-- Chapter: this is some stuff I added"
        output = innards.extract_inline_config(line)

        self.assertTrue(isinstance(output, dict))
        self.assertEqual(len(output), 0)

    def test_single_config(self):
        """Pull out a single config element.
        """
        line = "-- Chapter -- Title: This is a chapter title"
        output = innards.extract_inline_config(line)

        self.assertTrue(isinstance(output, dict))
        self.assertEqual(output["Title"], "This is a chapter title")
        self.assertEqual(len(output), 1)

    def test_multiple_config(self):
        """Pull out various config elements.
        """
        line = "-- Chapter -- Title: This is a chapter title -- Numbered: False"
        output = innards.extract_inline_config(line)

        self.assertTrue(isinstance(output, dict))
        self.assertEqual(output["Title"], "This is a chapter title")
        self.assertEqual(output["Numbered"], "False")
        self.assertEqual(len(output), 2)

    def test_multiple_config_with_irrelevant_text(self):
        """The function should be robust to some variation around the separator (in case I feel frisky).
        """
        line = "-- Chapter: This is some irrelevant text -- Title: This is a chapter title -- Numbered: False"
        output = innards.extract_inline_config(line)

        self.assertTrue(isinstance(output, dict))
        self.assertEqual(output["Title"], "This is a chapter title")
        self.assertEqual(output["Numbered"], "False")
        self.assertEqual(len(output), 2)


class TestConvertInlineConfigToSeparatorConfig(unittest.TestCase):
    def test_empty_dict(self):
        """Passing in an empty dictionary should return the default config for separators.
        """
        output = innards.convert_inline_config_to_separator_config({})

        # Given an empty dict, we should have an instance of SeparatorConfig that is initialised with the default but IS
        # NOT the same instance as the default.
        self.assertTrue(isinstance(output, Manuscript.SeparatorConfig))
        self.assertEqual(output, innards.SEPARATOR_CONFIG_DEFAULT)
        self.assertFalse(output is innards.SEPARATOR_CONFIG_DEFAULT)

    def test_nonsensical_dict(self):
        """Passing in a dict with weird keys should behave the same as an empty dict.
        """
        input = {"sOmE_wEiRd_kEy": "sOmE_wEiRd_vAlUe"}
        output = innards.convert_inline_config_to_separator_config(input)

        self.assertTrue(isinstance(output, Manuscript.SeparatorConfig))
        self.assertEqual(output, innards.SEPARATOR_CONFIG_DEFAULT)
        self.assertFalse(output is innards.SEPARATOR_CONFIG_DEFAULT)

    def test_title(self):
        """Gief title, get title
        """
        input = {"Title": "This is a chapter title"}
        output = innards.convert_inline_config_to_separator_config(input)

        self.assertTrue(isinstance(output, Manuscript.SeparatorConfig))
        self.assertEqual(output.title, "This is a chapter title")
        self.assertEqual(output.numbered, True)

    def test_title_and_numbered(self):
        """Gief title, get title
        """
        input = {"Title": "This is a chapter title", "Numbered": "False"}
        output = innards.convert_inline_config_to_separator_config(input)

        self.assertTrue(isinstance(output, Manuscript.SeparatorConfig))
        self.assertEqual(output.title, "This is a chapter title")
        self.assertEqual(output.numbered, False)


if __name__ == '__main__':
    unittest.main()