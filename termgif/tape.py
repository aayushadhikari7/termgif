"""Tape file parser - simple format for scripting terminal recordings."""
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class TypeAction:
    """Type text into terminal."""
    text: str


@dataclass
class EnterAction:
    """Press enter key."""
    pass


@dataclass
class SleepAction:
    """Wait for duration."""
    ms: int


@dataclass
class KeyAction:
    """Press a special key (for TUI interaction).

    Supported keys:
    - Navigation: up, down, left, right, home, end, pageup, pagedown
    - Editing: backspace, delete, tab, space
    - Control: escape, enter, return
    - Modifiers: ctrl+c, ctrl+d, ctrl+z, ctrl+l, alt+<key>
    - Function keys: f1-f12
    """
    key: str


@dataclass
class TapeConfig:
    """Recording configuration."""
    output: str = "output.gif"
    width: int = 80
    height: int = 24
    font_size: int = 14
    typing_speed_ms: int = 50
    loop: int = 0  # 0 = infinite, 1 = play once, N = play N times
    title: str = "termgif"  # Window title (customizable for your project)
    quality: int = 2  # Render scale (1=fast, 2=smooth, 3=ultra)
    chrome: bool = True  # Show window chrome (title bar, buttons)
    fps: int = 10  # Frames per second for terminal capture
    theme: str = "mocha"  # Color theme (mocha, latte, frappe, macchiato, dracula, nord)
    padding: int = 20  # Padding around content
    prompt: str = ""  # Custom prompt (empty = auto-generate)
    start_delay: int = 500  # Initial delay in ms
    end_delay: int = 2000  # Final frame hold in ms
    cursor: str = "block"  # Cursor style (block, bar, underline)
    radius: int = 10  # Corner radius for both inner and outer (0 = sharp)
    radius_outer: int | None = None  # Outer GIF edge radius (None = use radius)
    radius_inner: int | None = None  # Inner window radius (None = use radius)
    native_colors: bool = False  # Preserve TUI app's native colors (don't apply theme)


def parse_duration(s: str) -> int:
    """Parse duration string to milliseconds."""
    s = s.strip().lower()
    if s.endswith("ms"):
        return int(s[:-2])
    elif s.endswith("s"):
        return int(float(s[:-1]) * 1000)
    return int(s)


def parse_tape(path: Path) -> tuple[TapeConfig, list]:
    """Parse a tape file into config and actions."""
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
            actions.append(SleepAction(ms=duration))
            continue

    return config, actions
