"""Action dataclasses for termgif recordings."""
from dataclasses import dataclass


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
    duration_ms: int


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
class HideAction:
    """Pause frame capturing (recording continues but frames not saved)."""
    pass


@dataclass
class ShowAction:
    """Resume frame capturing."""
    pass


@dataclass
class ScreenshotAction:
    """Capture current frame as a separate PNG file."""
    filename: str


@dataclass
class MarkerAction:
    """Add a named marker/chapter at this point in the recording."""
    name: str


@dataclass
class RequireAction:
    """Check that a command/program exists before recording."""
    command: str


# Action type alias for type hints
Action = TypeAction | EnterAction | SleepAction | KeyAction | HideAction | ShowAction | ScreenshotAction | MarkerAction | RequireAction
