#!/usr/bin/env python3
"""Tracker entry point for the shared transactional campaign CLI.

Use pressure, clock, scene or beat with the same arguments as tools/play.py.
There is no generic editor for structured Pressure or its cycle history.
"""
from play import main


if __name__ == "__main__":
    raise SystemExit(main())
