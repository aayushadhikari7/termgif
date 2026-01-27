"""Core recording functionality for termgif."""
from .recorder import BaseRecorder
from .simulated import SimulatedRecorder, record_script
from .live import LiveRecorder, record_live
from .terminal import TerminalRecorder, record_terminal
from .session import LiveSession

__all__ = [
    'BaseRecorder',
    'SimulatedRecorder',
    'LiveRecorder',
    'TerminalRecorder',
    'LiveSession',
    'record_script',
    'record_live',
    'record_terminal',
]
