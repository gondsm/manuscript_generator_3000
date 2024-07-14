import unittest

# We need to start by adding the packages we're testing into the path, which is an unfortunate reality of not wanting to
# install the package just to run unit tests.
import test_utils
test_utils.finagle_dependencies()
from manuscript import Manuscript


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


if __name__ == '__main__':
    unittest.main()
