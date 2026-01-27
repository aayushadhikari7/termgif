"""Utility modules for termgif."""
from .keyboard import send_key, type_text, focus_terminal
from .window import get_terminal_window_rect
from .platform import is_windows, is_macos, is_linux
from .ffmpeg import check_ffmpeg, run_ffmpeg
from .share import upload, upload_imgur, upload_giphy, upload_catbox, ShareError
from .config_file import (
    load_config, get_config_value, create_default_config,
    get_config_dir, get_global_config_path, GlobalConfig,
)

__all__ = [
    'send_key',
    'type_text',
    'focus_terminal',
    'get_terminal_window_rect',
    'is_windows',
    'is_macos',
    'is_linux',
    'check_ffmpeg',
    'run_ffmpeg',
    'upload',
    'upload_imgur',
    'upload_giphy',
    'upload_catbox',
    'ShareError',
    'load_config',
    'get_config_value',
    'create_default_config',
    'get_config_dir',
    'get_global_config_path',
    'GlobalConfig',
]
