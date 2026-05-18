import sys
import os

# Add backend directory to Python path so imports like
# "from analysis.ensemble import ..." resolve correctly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
