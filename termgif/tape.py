"""Tape file parser - simple format for scripting terminal recordings.

This module provides backwards compatibility by re-exporting from
the new modular structure (config.py, actions.py, parser/).
"""
from pathlib import Path

# Re-export from new modules for backwards compatibility
from .config import TapeConfig, parse_duration
from .actions import TypeAction, EnterAction, SleepAction, KeyAction


def parse_tape(path: Path) -> tuple[TapeConfig, list]:
    """Parse a tape file into config and actions.

    This is a compatibility wrapper that delegates to the new parser module.
    """
    from .parser.tape import parse_tape as _parse_tape
    return _parse_tape(path)


__all__ = [
    'TapeConfig',
    'TypeAction',
    'EnterAction',
    'SleepAction',
    'KeyAction',
    'parse_duration',
    'parse_tape',
]
