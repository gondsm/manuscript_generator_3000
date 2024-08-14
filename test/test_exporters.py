import unittest

# We need to start by adding the packages we're testing into the path, which is an unfortunate reality of not wanting to
# install the package just to run unit tests.
import test_utils
test_utils.finagle_dependencies()

from manuscript_generator_3000.exporters import latex_pdf_exporter
from manuscript_generator_3000.exporters import markdown_exporter


class TestExporters(unittest.TestCase):
    def test_sunny_day(self):
        # It should be possible to import all of the above without anything exploding.
        pass


if __name__ == '__main__':
    unittest.main()