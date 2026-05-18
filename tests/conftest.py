import sys
from pathlib import Path

# Make `rules/` importable without packaging.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
