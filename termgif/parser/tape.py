"""Legacy .tape format parser."""
from pathlib import Path
import re

from ..config import TapeConfig, parse_duration
from ..actions import TypeAction, EnterAction, SleepAction


def parse_tape(path: Path) -> tuple[TapeConfig, list]:
    """Parse a legacy .tape file into config and actions.

    Args:
        path: Path to the .tape file

    Returns:
        (config, actions) tuple
    """
    config = TapeConfig()
    actions = []

    content = path.read_text()

    for line in content.splitlines():
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith("#"):
            continue

        # Output path
        if line.lower().startswith("output "):
            config.output = line[7:].strip().strip('"')
            continue

        # Settings
        if line.lower().startswith("set "):
            parts = line[4:].split(None, 1)
            if len(parts) == 2:
                key, value = parts[0].lower(), parts[1].strip().strip('"')
                if key == "width":
                    config.width = int(value)
                elif key == "height":
                    config.height = int(value)
                elif key == "fontsize":
                    config.font_size = int(value)
                elif key == "typingspeed":
                    config.typing_speed_ms = parse_duration(value)
            continue

        # Type command
        if line.lower().startswith("type "):
            match = re.match(r'type\s+"(.*)"\s*$', line, re.IGNORECASE)
            if match:
                actions.append(TypeAction(text=match.group(1)))
            continue

        # Enter key
        if line.lower() == "enter":
            actions.append(EnterAction())
            continue

        # Sleep
        if line.lower().startswith("sleep "):
            duration = parse_duration(line[6:])
            actions.append(SleepAction(duration_ms=duration))
            continue

    return config, actions
