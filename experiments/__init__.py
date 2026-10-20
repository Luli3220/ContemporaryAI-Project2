"""Reproducible experiments; this package also bootstraps an uninstalled checkout."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
