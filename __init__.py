# Pretty much all of the init files in this package do this path chicanery so they can import submodules. This is
# horrible and should not be necessary.
# TODO: sort out import system.
import sys
from pathlib import Path

package_path = Path(__file__).parent
sys.path.append(str(package_path))