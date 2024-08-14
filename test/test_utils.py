import sys
from pathlib import Path

def finagle_dependencies():
    sys.path.append(str(Path(__file__).parents[2]))