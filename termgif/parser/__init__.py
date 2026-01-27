"""Parser modules for termgif script formats."""
from pathlib import Path

from ..config import TapeConfig
from ..actions import Action
from .tg import parse_tg, TgParser, TgTokenizer
from .tape import parse_tape


def parse_script(path: Path) -> tuple[TapeConfig, list[Action]]:
    """Parse a script file (.tg or .tape).

    Args:
        path: Path to the script file

    Returns:
        (config, actions) tuple

    Raises:
        ValueError: If file type is unknown
    """
    suffix = path.suffix.lower()
    if suffix == ".tg":
        return parse_tg(path)
    elif suffix == ".tape":
        return parse_tape(path)
    else:
        raise ValueError(f"Unknown file type: {suffix}. Use .tg or .tape")


__all__ = [
    'parse_script',
    'parse_tg',
    'parse_tape',
    'TgParser',
    'TgTokenizer',
]
