"""termgif - Dead simple terminal GIF recorder.

A comprehensive terminal recording studio with multiple output formats,
live recording, editing capabilities, and a modular architecture.
"""

__version__ = "0.3.0"

# Re-export commonly used classes and functions
from .config import TapeConfig, parse_duration
from .actions import TypeAction, EnterAction, SleepAction, KeyAction, Action

# Backwards compatibility - also available from .tape
from .tape import parse_tape

__all__ = [
    '__version__',
    'TapeConfig',
    'parse_duration',
    'TypeAction',
    'EnterAction',
    'SleepAction',
    'KeyAction',
    'Action',
    'parse_tape',
]
