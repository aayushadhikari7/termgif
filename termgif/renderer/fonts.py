"""Font loading and management for terminal rendering."""
from PIL import ImageFont


def get_default_font_paths() -> list[str]:
    """Get list of default monospace font paths to try.

    Returns paths for common system fonts on Windows, macOS, and Linux.
    """
    return [
        # Windows
        "C:/Windows/Fonts/CascadiaCode.ttf",
        "C:/Windows/Fonts/CascadiaMono.ttf",
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/JetBrainsMono-Regular.ttf",
        "C:/Windows/Fonts/FiraCode-Regular.ttf",
        "C:/Windows/Fonts/SourceCodePro-Regular.ttf",
        # macOS
        "/System/Library/Fonts/SFMono.ttf",
        "/Library/Fonts/SF-Mono-Regular.otf",
        "/System/Library/Fonts/Monaco.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/Library/Fonts/JetBrainsMono-Regular.ttf",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/TTF/JetBrainsMono-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
        "/usr/share/fonts/truetype/firacode/FiraCode-Regular.ttf",
        "/usr/share/fonts/TTF/FiraCode-Regular.ttf",
        "/usr/share/fonts/truetype/hack/Hack-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]


def get_default_font_names() -> list[str]:
    """Get list of font names to try for cross-platform font loading.

    These are font family names that PIL can resolve on various systems.
    """
    return [
        "Cascadia Code",
        "Cascadia Mono",
        "JetBrains Mono",
        "Fira Code",
        "SF Mono",
        "Consolas",
        "Monaco",
        "Menlo",
        "DejaVu Sans Mono",
        "Ubuntu Mono",
        "Hack",
        "Liberation Mono",
        "Source Code Pro",
        "Courier New",
    ]


def get_font(size: int, font_path: str | None = None) -> ImageFont.FreeTypeFont:
    """Get a high-quality monospace font.

    Args:
        size: Font size in pixels
        font_path: Optional specific font path to use

    Returns:
        PIL FreeTypeFont object
    """
    # Try specific path if provided
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError):
            pass  # Fall through to default paths

    # Try font paths first
    for path in get_default_font_paths():
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue

    # Try font names
    for name in get_default_font_names():
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue

    # Last resort: default font
    return ImageFont.load_default()


def get_font_metrics(font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    """Get the metrics of a font (char width, line height).

    Args:
        font: PIL font object

    Returns:
        (char_width, line_height) tuple
    """
    # Use 'M' as reference for monospace width
    bbox = font.getbbox("M")
    char_width = bbox[2] - bbox[0]
    char_height = bbox[3] - bbox[1]

    return char_width, char_height
