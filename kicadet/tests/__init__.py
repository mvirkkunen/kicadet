import sys
from pathlib import Path

root = Path(__file__).parent.resolve().parent
sys.path.append(str(root.parent))

from .pcb_tests import *
