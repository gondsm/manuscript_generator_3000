import unittest

# We need to start by adding the packages we're testing into the path, which is an unfortunate reality of not wanting to
# install the package just to run unit tests.
import test_utils
test_utils.finagle_dependencies()

from manuscript_generator_3000.example import compile_example


class TestCompileExample(unittest.TestCase):
    def test_compile_example(self):
        """Run the example script as an integration test of sorts.
        """
        compile_example.compile()


if __name__ == '__main__':
    unittest.main()