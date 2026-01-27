"""Asciinema v2 format exporter and importer."""
from pathlib import Path
import json
import time
from PIL import Image

from .base import BaseExporter, register_exporter
from ..config import TapeConfig


@register_exporter
class AsciinemaExporter(BaseExporter):
    """Export recordings to asciinema v2 format (.cast files)."""

    format_name = "asciinema"
    extensions = [".cast"]
    requires_ffmpeg = False

    def export(self, output_path: Path) -> Path:
        """Export frames as asciinema v2 cast file.

        Note: This creates a simplified cast file from frame data.
        For full fidelity, use the text-based export during recording.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create header
        header = {
            "version": 2,
            "width": self.config.width,
            "height": self.config.height,
            "timestamp": int(time.time()),
            "env": {
                "SHELL": self.config.shell or "/bin/bash",
                "TERM": "xterm-256color"
            }
        }

        if self.config.title:
            header["title"] = self.config.title

        events = []
        current_time = 0.0

        # Convert frame durations to events
        # Note: Without actual terminal output data, we create placeholder events
        for i, duration_ms in enumerate(self.durations):
            # Each frame becomes an output event
            # In a real implementation, we'd have the actual terminal output
            event_time = current_time
            events.append([event_time, "o", f"[Frame {i + 1}]\r\n"])
            current_time += duration_ms / 1000.0

        # Write cast file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(header) + '\n')
            for event in events:
                f.write(json.dumps(event) + '\n')

        return output_path


class AsciinemaTextExporter:
    """Export actual terminal text to asciinema format.

    This exporter works with raw terminal output data rather than frames.
    """

    def __init__(self, width: int = 80, height: int = 24, title: str = ""):
        self.width = width
        self.height = height
        self.title = title
        self.events: list[tuple[float, str, str]] = []
        self.start_time: float | None = None

    def start(self):
        """Start recording."""
        self.start_time = time.time()
        self.events = []

    def add_output(self, text: str):
        """Add output event."""
        if self.start_time is None:
            self.start()
        elapsed = time.time() - self.start_time
        self.events.append((elapsed, "o", text))

    def add_input(self, text: str):
        """Add input event."""
        if self.start_time is None:
            self.start()
        elapsed = time.time() - self.start_time
        self.events.append((elapsed, "i", text))

    def export(self, output_path: Path) -> Path:
        """Export to cast file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        header = {
            "version": 2,
            "width": self.width,
            "height": self.height,
            "timestamp": int(self.start_time or time.time()),
            "env": {
                "SHELL": "/bin/bash",
                "TERM": "xterm-256color"
            }
        }

        if self.title:
            header["title"] = self.title

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(header) + '\n')
            for event_time, event_type, data in self.events:
                f.write(json.dumps([event_time, event_type, data]) + '\n')

        return output_path


def parse_cast_file(cast_path: Path) -> tuple[dict, list[tuple[float, str, str]]]:
    """Parse an asciinema v2 cast file.

    Args:
        cast_path: Path to the .cast file

    Returns:
        Tuple of (header dict, list of (time, type, data) events)
    """
    cast_path = Path(cast_path)

    with open(cast_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        raise ValueError("Empty cast file")

    # First line is header
    header = json.loads(lines[0])

    # Validate version
    if header.get("version") != 2:
        raise ValueError(f"Unsupported asciinema version: {header.get('version')}")

    # Parse events
    events = []
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        event = json.loads(line)
        if len(event) >= 3:
            events.append((float(event[0]), str(event[1]), str(event[2])))

    return header, events


def import_cast_to_config(cast_path: Path) -> tuple[TapeConfig, list]:
    """Import a cast file and convert to TapeConfig and actions.

    Args:
        cast_path: Path to the .cast file

    Returns:
        Tuple of (TapeConfig, list of actions)
    """
    from ..actions import TypeAction, SleepAction, EnterAction

    header, events = parse_cast_file(cast_path)

    config = TapeConfig(
        width=header.get("width", 80),
        height=header.get("height", 24),
        title=header.get("title", ""),
    )

    actions = []
    last_time = 0.0

    for event_time, event_type, data in events:
        # Add sleep if there's a gap
        gap = event_time - last_time
        if gap > 0.05:  # 50ms threshold
            actions.append(SleepAction(duration_ms=int(gap * 1000)))

        if event_type == "o":  # Output
            # Convert output to type actions (simplified)
            # In reality, output is what the terminal shows, not input
            # But we can try to reconstruct input from it
            if data.endswith('\r\n') or data.endswith('\n'):
                text = data.rstrip('\r\n')
                if text:
                    actions.append(TypeAction(text=text))
                actions.append(EnterAction())
            elif data:
                actions.append(TypeAction(text=data))

        elif event_type == "i":  # Input
            if data == '\r' or data == '\n':
                actions.append(EnterAction())
            else:
                actions.append(TypeAction(text=data))

        last_time = event_time

    return config, actions


def render_cast_to_frames(
    cast_path: Path,
    config: TapeConfig | None = None,
) -> tuple[list[Image.Image], list[int]]:
    """Render a cast file to image frames.

    Args:
        cast_path: Path to the .cast file
        config: Optional TapeConfig for rendering settings

    Returns:
        Tuple of (list of PIL Images, list of durations in ms)
    """
    from ..renderer.terminal import TerminalRenderer
    from ..renderer.styles import TerminalStyle
    from ..pty.emulator import TerminalEmulator

    header, events = parse_cast_file(cast_path)

    width = header.get("width", 80)
    height = header.get("height", 24)

    if config is None:
        config = TapeConfig(width=width, height=height)
    else:
        config.width = width
        config.height = height

    # Create TerminalStyle from TapeConfig
    style = TerminalStyle(
        width=config.width,
        height=config.height,
        font_size=config.font_size,
        padding=config.padding,
        title=config.title or header.get("title", "termgif"),
        theme=config.theme,
    )

    # Create renderer and emulator
    renderer = TerminalRenderer(style)
    emulator = TerminalEmulator(width, height)

    frames = []
    durations = []

    # Group events by time windows (e.g., 100ms)
    frame_interval = 1000 / config.fps  # ms per frame
    current_frame_time = 0.0
    pending_output = ""

    for i, (event_time, event_type, data) in enumerate(events):
        event_time_ms = event_time * 1000

        # If we've passed the frame boundary, render a frame
        while event_time_ms >= current_frame_time + frame_interval:
            if pending_output:
                emulator.feed(pending_output)
                pending_output = ""

            # Render current state
            frame = renderer.render_lines(emulator.get_lines())
            frames.append(frame)
            durations.append(int(frame_interval))
            current_frame_time += frame_interval

        # Accumulate output
        if event_type == "o":
            pending_output += data

    # Render final frame if there's pending output
    if pending_output:
        emulator.feed(pending_output)
        frame = renderer.render_lines(emulator.get_lines())
        frames.append(frame)
        durations.append(int(frame_interval))

    # Ensure we have at least one frame
    if not frames:
        frame = renderer.render_lines(emulator.get_lines())
        frames.append(frame)
        durations.append(1000)

    return frames, durations


__all__ = [
    'AsciinemaExporter',
    'AsciinemaTextExporter',
    'parse_cast_file',
    'import_cast_to_config',
    'render_cast_to_frames',
]
