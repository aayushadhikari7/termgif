"""Editing tools for termgif recordings."""
from .trim import trim_recording
from .speed import change_speed
from .concat import concatenate
from .overlay import add_watermark, add_caption

__all__ = [
    'trim_recording',
    'change_speed',
    'concatenate',
    'add_watermark',
    'add_caption',
]
