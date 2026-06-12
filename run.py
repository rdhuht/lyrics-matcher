"""Entry point for PyInstaller."""

import sys
import os

# Add src to path for direct import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lyrics_matcher.gui import LyricsMatcherGUI


def main():
    """Main entry point."""
    app = LyricsMatcherGUI()
    app.run()


if __name__ == "__main__":
    main()