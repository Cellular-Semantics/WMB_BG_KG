"""
Centralized path management utility for the WMB_BG_KG project.
All scripts should use this for consistent path handling.
"""
from pathlib import Path
import sys

def get_project_root():
    """Find project root by looking for Makefile or .git directory."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / 'Makefile').exists() or (parent / '.git').exists():
            return parent
    raise RuntimeError("Could not find project root")

def setup_project_path():
    """Add project root to sys.path if not already there."""
    root = get_project_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root

# Global project root - computed once when module is imported
PROJECT_ROOT = get_project_root()

# Common project paths
RESOURCES_DIR = PROJECT_ROOT / 'resources'
CONFIG_DIR = PROJECT_ROOT / 'config'
SRC_DIR = PROJECT_ROOT / 'src'
TEMPLATES_DIR = SRC_DIR / 'templates'
REPORTS_DIR = PROJECT_ROOT / 'reports'
OWL_DIR = PROJECT_ROOT / 'owl'
CYPHER_DIR = SRC_DIR / 'cypher'