"""Terminal style definitions and state management."""
from dataclasses import dataclass, field
import os


@dataclass
class TerminalStyle:
    """Terminal appearance settings."""
    width: int = 80
    height: int = 24
    font_size: int = 14
    padding: int = 20
    line_height: float = 1.4
    title: str = "termgif"
    chrome: bool = True
    theme: str = "mocha"
    prompt: str = ""  # Custom prompt
    user: str = ""  # Username in prompt (empty = auto-detect)
    hostname: str = ""  # Hostname/folder in prompt (empty = auto-detect)
    symbol: str = "$"  # Prompt symbol ($ for user, # for root)

    cursor: str = "block"  # block, bar, underline

    # Window chrome
    title_bar_height: int = 52
    button_radius: int = 7
    button_spacing: int = 9
    corner_radius: int = 12  # Inner window corner radius
    outer_radius: int = 10   # Outer GIF edge radius

    # Quality settings
    scale: int = 2
    shadow_blur: int = 25
    shadow_offset: int = 8


@dataclass
class StyledCell:
    """A cell with styling info for native color rendering."""
    char: str = " "
    fg: str = "text"
    bg: str = "base"
    bold: bool = False


@dataclass
class TerminalState:
    """Current state of the terminal."""
    lines: list[str] = field(default_factory=list)
    current_line: str = ""
    prompt: str = ""
    cwd: str = ""
    # Styled lines for native color mode (list of lists of StyledCell)
    styled_lines: list[list[StyledCell]] | None = None
    # Custom user/hostname/symbol for prompt
    custom_user: str = ""
    custom_hostname: str = ""
    custom_symbol: str = "$"

    def __post_init__(self):
        self.cwd = os.getcwd()
        self._update_prompt()
        self.current_line = self.prompt

    def _update_prompt(self):
        user = self.custom_user or os.environ.get("USER", os.environ.get("USERNAME", "user"))
        hostname = self.custom_hostname or os.path.basename(self.cwd) or "~"
        symbol = self.custom_symbol or "$"
        self.prompt = f"{user}@{hostname} {symbol} "


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple.

    Args:
        hex_color: Hex color string like "#rrggbb"

    Returns:
        (r, g, b) tuple
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values to hex color.

    Args:
        r: Red component (0-255)
        g: Green component (0-255)
        b: Blue component (0-255)

    Returns:
        Hex color string like "#rrggbb"
    """
    return f"#{r:02x}{g:02x}{b:02x}"


def create_rounded_rectangle_mask(size: tuple[int, int], radius: int):
    """Create an anti-aliased rounded rectangle mask.

    Args:
        size: (width, height) tuple
        radius: Corner radius in pixels

    Returns:
        PIL Image in 'L' mode (grayscale)
    """
    from PIL import Image, ImageDraw

    # Create at higher resolution for smoother edges
    scale = 4
    w, h = size[0] * scale, size[1] * scale
    r = radius * scale

    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)

    # Draw rounded rectangle
    draw.rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)

    # Scale down with anti-aliasing
    return mask.resize(size, Image.LANCZOS)
