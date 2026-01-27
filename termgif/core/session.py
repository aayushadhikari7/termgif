"""Live session recording - record actual terminal sessions without scripts."""
import os
import sys
import time
import signal
import threading
from pathlib import Path
from typing import Callable

from PIL import Image, ImageGrab

from ..config import TapeConfig
from ..utils.window import get_terminal_window_rect


class LiveSession:
    """Record actual terminal session without a script.

    Captures the terminal window in real-time, with support for
    pause/resume functionality via hotkeys.
    """

    def __init__(
        self,
        output: str | Path = "session.gif",
        fps: int = 10,
        duration: int | None = None,
        width: int = 80,
        height: int = 24,
        config: TapeConfig | None = None,
    ):
        """Initialize live session recorder.

        Args:
            output: Output file path
            fps: Frames per second
            duration: Maximum recording duration in seconds (None = no limit)
            width: Terminal width in characters
            height: Terminal height in characters
            config: Optional TapeConfig for additional settings
        """
        self.output = Path(output)
        self.fps = fps
        self.frame_duration = 1000 // fps
        self.max_duration = duration
        self.width = width
        self.height = height
        self.config = config or TapeConfig()

        self.frames: list[Image.Image] = []
        self.frame_durations: list[int] = []
        self.bbox = None
        self.expected_size = None
        self.last_valid_frame = None

        self._recording = False
        self._paused = False
        self._stop_event = threading.Event()
        self._capture_thread = None

        # Callbacks
        self.on_start: Callable[[], None] | None = None
        self.on_stop: Callable[[], None] | None = None
        self.on_pause: Callable[[], None] | None = None
        self.on_resume: Callable[[], None] | None = None
        self.on_frame: Callable[[int], None] | None = None

    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording and not self._paused

    @property
    def is_paused(self) -> bool:
        """Check if recording is paused."""
        return self._paused

    @property
    def frame_count(self) -> int:
        """Get current frame count."""
        return len(self.frames)

    @property
    def elapsed_time(self) -> float:
        """Get elapsed recording time in seconds."""
        return sum(self.frame_durations) / 1000

    def _detect_window(self) -> bool:
        """Detect terminal window region."""
        try:
            region = get_terminal_window_rect()
            if region:
                x, y, w, h = region
                if w > 0 and h > 0:
                    self.bbox = (x, y, x + w, y + h)
                    return True
        except Exception:
            pass

        self.bbox = None
        return False

    def _capture_frame(self) -> bool:
        """Capture a single frame."""
        try:
            frame = ImageGrab.grab(bbox=self.bbox)

            if frame.size[0] == 0 or frame.size[1] == 0:
                if self.last_valid_frame:
                    self.frames.append(self.last_valid_frame.copy())
                    self.frame_durations.append(self.frame_duration)
                    return True
                return False

            if frame.mode != "RGB":
                frame = frame.convert("RGB")
            frame = frame.copy()

            if self.expected_size is None:
                self.expected_size = frame.size

            if frame.size != self.expected_size:
                if self.last_valid_frame:
                    self.frames.append(self.last_valid_frame.copy())
                    self.frame_durations.append(self.frame_duration)
                    return True
                frame = frame.resize(self.expected_size, Image.Resampling.LANCZOS)

            self.last_valid_frame = frame.copy()
            self.frames.append(frame)
            self.frame_durations.append(self.frame_duration)

            if self.on_frame:
                self.on_frame(len(self.frames))

            return True

        except Exception:
            if self.last_valid_frame:
                self.frames.append(self.last_valid_frame.copy())
                self.frame_durations.append(self.frame_duration)
                return True
            return False

    def _capture_loop(self):
        """Main capture loop running in background thread."""
        start_time = time.time()

        while not self._stop_event.is_set():
            # Check duration limit
            if self.max_duration and (time.time() - start_time) >= self.max_duration:
                break

            # Skip if paused
            if self._paused:
                time.sleep(0.1)
                continue

            # Capture frame
            self._capture_frame()

            # Wait for next frame
            time.sleep(self.frame_duration / 1000)

    def start(self) -> bool:
        """Start recording session.

        Returns:
            True if recording started successfully
        """
        if self._recording:
            return False

        # Detect window
        if not self._detect_window():
            print("[Warning: Could not detect terminal window, capturing full screen]")

        self._recording = True
        self._paused = False
        self._stop_event.clear()

        # Start capture thread
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()

        if self.on_start:
            self.on_start()

        return True

    def stop(self) -> Path:
        """Stop recording and save output.

        Returns:
            Path to the saved file
        """
        if not self._recording:
            raise RuntimeError("Not recording")

        self._stop_event.set()
        self._recording = False

        if self._capture_thread:
            self._capture_thread.join(timeout=2.0)
            self._capture_thread = None

        if self.on_stop:
            self.on_stop()

        # Save the recording
        return self.save()

    def pause(self) -> None:
        """Pause recording."""
        if self._recording and not self._paused:
            self._paused = True
            if self.on_pause:
                self.on_pause()

    def resume(self) -> None:
        """Resume recording."""
        if self._recording and self._paused:
            self._paused = False
            if self.on_resume:
                self.on_resume()

    def toggle_pause(self) -> None:
        """Toggle pause state."""
        if self._paused:
            self.resume()
        else:
            self.pause()

    def save(self) -> Path:
        """Save captured frames to output file.

        Returns:
            Path to the saved file
        """
        if not self.frames:
            raise ValueError("No frames captured")

        from ..exporters import get_exporter, detect_format

        format_type = detect_format(self.output, self.config)
        exporter_class = get_exporter(format_type)
        exporter = exporter_class(self.frames, self.frame_durations, self.config)

        return exporter.export(self.output)


def record_live_session(
    output: str | Path = "session.gif",
    fps: int = 10,
    duration: int | None = None,
) -> Path:
    """Start an interactive live recording session.

    Args:
        output: Output file path
        fps: Frames per second
        duration: Maximum duration in seconds

    Returns:
        Path to the saved file
    """
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel

    console = Console()

    session = LiveSession(output=output, fps=fps, duration=duration)

    # Status display
    def get_status():
        status = "RECORDING" if session.is_recording else "PAUSED" if session.is_paused else "STOPPED"
        color = "red" if session.is_recording else "yellow" if session.is_paused else "dim"
        return Panel(
            f"[{color}]{status}[/] | "
            f"Frames: {session.frame_count} | "
            f"Time: {session.elapsed_time:.1f}s\n"
            f"[dim]Press Ctrl+C to stop[/]",
            title="termgif live",
            border_style=color,
        )

    console.print("\n[bold cyan]termgif live recording[/]")
    console.print("[dim]Starting in 3 seconds... Position your terminal window.[/]\n")

    # Countdown
    for i in range(3, 0, -1):
        console.print(f"[yellow]{i}...[/]")
        time.sleep(1)

    session.start()

    try:
        with Live(get_status(), console=console, refresh_per_second=4) as live:
            while session._recording:
                live.update(get_status())
                time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        if session._recording:
            output_path = session.stop()
            console.print(f"\n[green]Saved to {output_path}[/]")
            return output_path

    return session.output
