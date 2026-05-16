"""
Standalone script to trigger recursive self-improvement.
Run: python scripts/self_improve.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.main import recursive_improvement

if __name__ == "__main__":
    recursive_improvement()
