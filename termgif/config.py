"""Configuration classes for termgif recordings."""
from dataclasses import dataclass


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

    # New v0.3.0 options
    format: str = "gif"  # Output format (gif, webp, mp4, webm, apng, svg, frames)
    bitrate: str = "2M"  # Video bitrate for mp4/webm
    codec: str = "h264"  # Video codec
    crf: int = 23  # Constant rate factor (quality) for video
    dither: str = "floyd-steinberg"  # GIF dithering algorithm
    colors: int = 256  # Max colors for GIF palette
    optimize: bool = True  # Optimize output size
    lossy: int = 100  # Lossy quality for WebP/video (0-100)
    preview: bool = False  # Generate preview thumbnail
    parallel: bool = False  # Parallel frame rendering
    watermark: str = ""  # Watermark image path
    watermark_position: str = "bottom-right"  # tl/tr/bl/br
    watermark_opacity: float = 0.5  # Watermark opacity
    caption: str = ""  # Caption text
    caption_position: str = "bottom"  # top/bottom
    shell: str = ""  # Shell to use
    env: list[str] | None = None  # Environment variables
    cwd: str = ""  # Working directory
    timeout: int = 30000  # Command timeout in ms


def parse_duration(s: str) -> int:
    """Parse duration string to milliseconds.

    Supports formats:
    - "500" or "500ms" -> 500 milliseconds
    - "1s" or "1.5s" -> 1000 or 1500 milliseconds
    """
    s = s.strip().lower()
    if s.endswith("ms"):
        return int(s[:-2])
    elif s.endswith("s"):
        return int(float(s[:-1]) * 1000)
    return int(s)
