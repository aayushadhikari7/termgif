"""Preview and playback functionality for terminal recordings."""
from pathlib import Path
import time
import sys
from typing import Optional

from PIL import Image
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def play_gif_in_terminal(
    gif_path: Path,
    loop: bool = True,
    max_width: Optional[int] = None,
    use_unicode: bool = True,
) -> None:
    """Play a GIF animation in the terminal using ASCII/Unicode art.

    Args:
        gif_path: Path to the GIF file
        loop: Whether to loop the animation
        max_width: Maximum width in characters (None for auto)
        use_unicode: Use Unicode block characters for better quality
    """
    console = Console()
    gif_path = Path(gif_path)

    if not gif_path.exists():
        console.print(f"[red]File not found: {gif_path}[/]")
        return

    img = Image.open(gif_path)

    # Get terminal size
    term_width = console.width or 80
    term_height = (console.height or 24) - 2  # Leave room for status

    if max_width:
        term_width = min(term_width, max_width)

    # Calculate aspect ratio
    # Each character is roughly 2x1 in aspect ratio
    char_aspect = 2.0

    frames = []
    durations = []

    try:
        while True:
            frame = img.copy().convert('RGB')

            # Calculate dimensions
            img_width, img_height = frame.size
            img_aspect = img_width / img_height

            # Target dimensions in characters
            # Width in chars, height in chars (accounting for char aspect)
            target_width = term_width
            target_height = int(target_width / img_aspect / char_aspect)

            if target_height > term_height:
                target_height = term_height
                target_width = int(target_height * img_aspect * char_aspect)

            # Resize image
            if use_unicode:
                # For Unicode blocks, we need 2 pixels per character vertically
                resized = frame.resize((target_width, target_height * 2), Image.Resampling.LANCZOS)
            else:
                resized = frame.resize((target_width, target_height), Image.Resampling.LANCZOS)

            frames.append(resized)
            durations.append(img.info.get('duration', 100))

            img.seek(img.tell() + 1)
    except EOFError:
        pass

    if not frames:
        console.print("[red]No frames found in GIF[/]")
        return

    # Play animation
    console.print(f"[dim]Playing {gif_path.name} ({len(frames)} frames). Press Ctrl+C to stop.[/]")

    try:
        frame_num = 0
        while True:
            frame = frames[frame_num]
            duration = durations[frame_num]

            # Convert to text
            if use_unicode:
                text = _image_to_unicode_blocks(frame)
            else:
                text = _image_to_ascii(frame)

            # Clear screen and print frame
            console.clear()
            console.print(text, end='')
            console.print(f"\n[dim]Frame {frame_num + 1}/{len(frames)}[/]")

            time.sleep(duration / 1000.0)

            frame_num += 1
            if frame_num >= len(frames):
                if loop:
                    frame_num = 0
                else:
                    break

    except KeyboardInterrupt:
        console.clear()
        console.print("[yellow]Playback stopped[/]")


def _image_to_ascii(img: Image.Image) -> str:
    """Convert an image to ASCII art."""
    # ASCII characters from dark to light
    chars = " .:-=+*#%@"

    pixels = img.load()
    width, height = img.size

    lines = []
    for y in range(height):
        line = ""
        for x in range(width):
            r, g, b = pixels[x, y]
            # Convert to grayscale
            gray = int(0.299 * r + 0.587 * g + 0.114 * b)
            # Map to character
            char_idx = int(gray / 256 * len(chars))
            char_idx = min(char_idx, len(chars) - 1)
            line += chars[char_idx]
        lines.append(line)

    return '\n'.join(lines)


def _image_to_unicode_blocks(img: Image.Image) -> str:
    """Convert an image to Unicode block characters with colors.

    Uses the upper half block character (U+2580) to display
    two pixels per character cell.
    """
    pixels = img.load()
    width, height = img.size

    lines = []
    for y in range(0, height - 1, 2):
        line = ""
        for x in range(width):
            # Top pixel
            r1, g1, b1 = pixels[x, y]
            # Bottom pixel
            r2, g2, b2 = pixels[x, y + 1]

            # Use ANSI 24-bit color
            # Upper half block with fg=top color, bg=bottom color
            line += f"\033[38;2;{r1};{g1};{b1}m\033[48;2;{r2};{g2};{b2}m\u2580"

        line += "\033[0m"  # Reset
        lines.append(line)

    return '\n'.join(lines)


def preview_script(
    script_path: Path,
    console: Optional[Console] = None,
) -> None:
    """Preview a script file without recording.

    Shows what actions will be performed.

    Args:
        script_path: Path to the script file
        console: Optional Rich console
    """
    if console is None:
        console = Console()

    script_path = Path(script_path)

    if not script_path.exists():
        console.print(f"[red]File not found: {script_path}[/]")
        return

    # Parse the script
    from .parser import parse_script
    config, actions = parse_script(script_path)

    # Display config
    console.print(Panel(
        f"[bold]Output:[/] {config.output}\n"
        f"[bold]Size:[/] {config.width}x{config.height}\n"
        f"[bold]Theme:[/] {config.theme}\n"
        f"[bold]FPS:[/] {config.fps}\n"
        f"[bold]Title:[/] {config.title or '(none)'}",
        title=f"Script: {script_path.name}",
        border_style="blue"
    ))

    # Display actions
    console.print("\n[bold]Actions:[/]")

    for i, action in enumerate(actions, 1):
        action_type = type(action).__name__

        if hasattr(action, 'text'):
            console.print(f"  {i:3}. [cyan]{action_type}[/]: [green]{repr(action.text)}[/]")
        elif hasattr(action, 'duration_ms'):
            console.print(f"  {i:3}. [cyan]{action_type}[/]: {action.duration_ms}ms")
        elif hasattr(action, 'key'):
            console.print(f"  {i:3}. [cyan]{action_type}[/]: {action.key}")
        else:
            console.print(f"  {i:3}. [cyan]{action_type}[/]")

    console.print(f"\n[dim]Total: {len(actions)} actions[/]")


def get_file_info(file_path: Path) -> dict:
    """Get information about a recording file.

    Args:
        file_path: Path to the file

    Returns:
        Dict with file information
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    info = {
        'path': str(file_path),
        'name': file_path.name,
        'size_bytes': file_path.stat().st_size,
        'format': file_path.suffix.lower().lstrip('.'),
    }

    # Get image/animation info
    try:
        img = Image.open(file_path)
        info['width'] = img.width
        info['height'] = img.height
        info['mode'] = img.mode

        # Count frames
        frame_count = 0
        total_duration = 0
        try:
            while True:
                frame_count += 1
                total_duration += img.info.get('duration', 100)
                img.seek(img.tell() + 1)
        except EOFError:
            pass

        info['frames'] = frame_count
        info['duration_ms'] = total_duration
        info['duration_s'] = total_duration / 1000.0

        if frame_count > 1:
            info['fps'] = frame_count / (total_duration / 1000.0)

    except Exception as e:
        info['error'] = str(e)

    return info


def print_file_info(file_path: Path, console: Optional[Console] = None) -> None:
    """Print information about a recording file.

    Args:
        file_path: Path to the file
        console: Optional Rich console
    """
    if console is None:
        console = Console()

    try:
        info = get_file_info(file_path)
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/]")
        return

    # Format size
    size = info['size_bytes']
    if size < 1024:
        size_str = f"{size} B"
    elif size < 1024 * 1024:
        size_str = f"{size / 1024:.1f} KB"
    else:
        size_str = f"{size / 1024 / 1024:.1f} MB"

    text = Text()
    text.append(f"File: ", style="bold")
    text.append(f"{info['name']}\n")
    text.append(f"Format: ", style="bold")
    text.append(f"{info['format'].upper()}\n")
    text.append(f"Size: ", style="bold")
    text.append(f"{size_str}\n")

    if 'width' in info:
        text.append(f"Dimensions: ", style="bold")
        text.append(f"{info['width']}x{info['height']}\n")

    if 'frames' in info:
        text.append(f"Frames: ", style="bold")
        text.append(f"{info['frames']}\n")

    if 'duration_s' in info:
        text.append(f"Duration: ", style="bold")
        text.append(f"{info['duration_s']:.2f}s\n")

    if 'fps' in info:
        text.append(f"FPS: ", style="bold")
        text.append(f"{info['fps']:.1f}\n")

    console.print(Panel(text, title="File Info", border_style="blue"))


__all__ = [
    'play_gif_in_terminal',
    'preview_script',
    'get_file_info',
    'print_file_info',
]
