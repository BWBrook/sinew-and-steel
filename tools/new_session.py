#!/usr/bin/env python3
"""Begin the next session after play.py session-close has recorded its end."""
import sys
from play import main


if __name__ == "__main__":
    raise SystemExit(main(["session", *sys.argv[1:]]))
