import unittest

# We need to start by adding the packages we're testing into the path, which is an unfortunate reality of not wanting to
# install the package just to run unit tests.
import test_utils
test_utils.finagle_dependencies()

from manuscript_generator_3000.exporters.epub_exporter import manually_number_markdown


class TestManuallyNumberMarkdown(unittest.TestCase):
    def test_single_part(self):
        """A single part should be numbered 1."""
        markdown_lines = ["# Part Title"]
        result = manually_number_markdown(markdown_lines)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "# 1. Part Title {-}")

    def test_multiple_parts(self):
        """Multiple parts should be numbered sequentially."""
        markdown_lines = ["# Part One", "# Part Two", "# Part Three"]
        result = manually_number_markdown(markdown_lines)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "# 1. Part One {-}")
        self.assertEqual(result[1], "# 2. Part Two {-}")
        self.assertEqual(result[2], "# 3. Part Three {-}")

    def test_chapters_within_parts(self):
        """Chapters should be numbered sequentially within each part (1, 2, then resets for next part)."""
        markdown_lines = [
            "# Part One",
            "## Chapter 1A",
            "## Chapter 1B",
            "# Part Two",
            "## Chapter 2A",
        ]
        result = manually_number_markdown(markdown_lines)
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0], "# 1. Part One {-}")
        self.assertEqual(result[1], "## 1 Chapter 1A {-}")
        self.assertEqual(result[2], "## 2 Chapter 1B {-}")
        self.assertEqual(result[3], "# 2. Part Two {-}")
        self.assertEqual(result[4], "## 1 Chapter 2A {-}")

    def test_chapter_counter_resets_per_part(self):
        """Chapter counter should reset when moving to a new part."""
        markdown_lines = [
            "# Part One",
            "## Chapter A",
            "## Chapter B",
            "# Part Two",
            "## Chapter A",
        ]
        result = manually_number_markdown(markdown_lines)
        self.assertEqual(result[1], "## 1 Chapter A {-}")
        self.assertEqual(result[2], "## 2 Chapter B {-}")
        self.assertEqual(result[4], "## 1 Chapter A {-}")

    def test_unnumbered_part(self):
        """Parts with {.unnumbered} should not be numbered or get {-}."""
        markdown_lines = ["# Part {.unnumbered}"]
        result = manually_number_markdown(markdown_lines)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "# Part {.unnumbered}")

    def test_unnumbered_chapter(self):
        """Chapters with {.unnumbered} should not be numbered or get {-}."""
        markdown_lines = [
            "# Part One",
            "## Chapter {.unnumbered}",
            "## Chapter After",
        ]
        result = manually_number_markdown(markdown_lines)
        self.assertEqual(result[0], "# 1. Part One {-}")
        self.assertEqual(result[1], "## Chapter {.unnumbered}")
        self.assertEqual(result[2], "## 1 Chapter After {-}")

    def test_mixed_numbered_and_unnumbered(self):
        """Mix of numbered and unnumbered parts/chapters should work correctly."""
        markdown_lines = [
            "# Part One",
            "## Chapter Normal",
            "## Chapter {.unnumbered}",
            "## Chapter Again",
            "# Part Two {.unnumbered}",
            "## Chapter in Unnumbered",
        ]
        result = manually_number_markdown(markdown_lines)
        self.assertEqual(result[0], "# 1. Part One {-}")
        self.assertEqual(result[1], "## 1 Chapter Normal {-}")
        self.assertEqual(result[2], "## Chapter {.unnumbered}")
        self.assertEqual(result[3], "## 2 Chapter Again {-}")
        self.assertEqual(result[4], "# Part Two {.unnumbered}")
        # When an unnumbered part is encountered, part_counter doesn't increment, so chapters keep the previous part's prefix
        self.assertEqual(result[5], "## 3 Chapter in Unnumbered {-}")

    def test_non_header_lines_passed_through(self):
        """Non-header lines should be passed through unchanged."""
        markdown_lines = [
            "# Part",
            "This is body text.",
            "More text here.",
            "## Chapter",
            "Even more text.",
        ]
        result = manually_number_markdown(markdown_lines)
        self.assertEqual(len(result), 5)
        self.assertEqual(result[1], "This is body text.")
        self.assertEqual(result[2], "More text here.")
        self.assertEqual(result[4], "Even more text.")

    def test_headers_with_leading_whitespace(self):
        """Headers with leading whitespace should work correctly."""
        markdown_lines = [
            "  # Part",
            "    ## Chapter",
        ]
        result = manually_number_markdown(markdown_lines)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "# 1. Part {-}")
        self.assertEqual(result[1], "## 1 Chapter {-}")

    def test_empty_input(self):
        """Empty input should return empty output."""
        markdown_lines = []
        result = manually_number_markdown(markdown_lines)
        self.assertEqual(len(result), 0)

    def test_only_body_text(self):
        """Input with no headers should pass through unchanged."""
        markdown_lines = [
            "Just some text.",
            "More text.",
            "",
            "Final text.",
        ]
        result = manually_number_markdown(markdown_lines)
        self.assertEqual(result, markdown_lines)

    def test_complex_realistic_manuscript(self):
        """Test a realistic manuscript structure with multiple parts and chapters."""
        markdown_lines = [
            "# Introduction {.unnumbered}",
            "This is the introduction.",
            "# Part One",
            "## Chapter One",
            "Content of chapter one.",
            "## Chapter Two",
            "Content of chapter two.",
            "# Part Two",
            "## Chapter One {.unnumbered}",
            "This chapter is unnumbered.",
            "## Chapter Two",
            "Real chapter content here.",
            "# Epilogue {.unnumbered}",
        ]
        result = manually_number_markdown(markdown_lines)
        
        self.assertEqual(result[0], "# Introduction {.unnumbered}")
        self.assertEqual(result[1], "This is the introduction.")
        self.assertEqual(result[2], "# 1. Part One {-}")
        self.assertEqual(result[3], "## 1 Chapter One {-}")
        self.assertEqual(result[4], "Content of chapter one.")
        self.assertEqual(result[5], "## 2 Chapter Two {-}")
        self.assertEqual(result[6], "Content of chapter two.")
        self.assertEqual(result[7], "# 2. Part Two {-}")
        self.assertEqual(result[8], "## Chapter One {.unnumbered}")
        self.assertEqual(result[9], "This chapter is unnumbered.")
        self.assertEqual(result[10], "## 1 Chapter Two {-}")
        self.assertEqual(result[11], "Real chapter content here.")
        self.assertEqual(result[12], "# Epilogue {.unnumbered}")


if __name__ == '__main__':
    unittest.main()
