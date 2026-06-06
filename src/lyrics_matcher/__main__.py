"""Main entry point for Lyrics Matcher."""

import sys


def main():
    """Main entry point."""
    from .gui import LyricsMatcherGUI

    app = LyricsMatcherGUI()
    app.run()


if __name__ == "__main__":
    main()