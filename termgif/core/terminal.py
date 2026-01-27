"""Terminal capture recorder - screen captures actual terminal window."""
import os
import sys
import time
import subprocess
from pathlib import Path
from PIL import Image, ImageGrab, ImageDraw

from ..config import TapeConfig
from ..actions import Action, TypeAction, EnterAction, SleepAction, KeyAction
from ..utils.keyboard import send_key, focus_terminal, _reset_terminal_hwnd, _get_terminal_hwnd
from ..utils.window import get_terminal_window_rect


# Screen capture support
HAS_CAPTURE = True
try:
    ImageGrab.grab(bbox=(0, 0, 1, 1))
except Exception:
    HAS_CAPTURE = False


def apply_rounded_corners(frame: Image.Image, radius: int, bg_color: tuple = (30, 30, 46)) -> Image.Image:
    """Apply rounded corners to a frame.

    Args:
        frame: The frame to apply rounded corners to
        radius: Corner radius in pixels
        bg_color: RGB background color for corners

    Returns:
        RGB image with rounded corners
    """
    if radius <= 0:
        return frame

    w, h = frame.size
    radius = min(radius, w // 2, h // 2)
    if radius <= 0:
        return frame

    if frame.mode != "RGB":
        frame = frame.convert("RGB")

    # Create rounded rectangle mask
    mask = Image.new("L", (w, h), 255)
    mask_draw = ImageDraw.Draw(mask)

    # Draw black corners
    mask_draw.rectangle([0, 0, radius, radius], fill=0)
    mask_draw.ellipse([0, 0, radius * 2, radius * 2], fill=255)

    mask_draw.rectangle([w - radius, 0, w, radius], fill=0)
    mask_draw.ellipse([w - radius * 2, 0, w, radius * 2], fill=255)

    mask_draw.rectangle([0, h - radius, radius, h], fill=0)
    mask_draw.ellipse([0, h - radius * 2, radius * 2, h], fill=255)

    mask_draw.rectangle([w - radius, h - radius, w, h], fill=0)
    mask_draw.ellipse([w - radius * 2, h - radius * 2, w, h], fill=255)

    bg = Image.new("RGB", (w, h), bg_color)
    result = Image.composite(frame, bg, mask)

    return result


class TerminalRecorder:
    """Records the actual terminal window via screen capture.

    Supports TUI applications through keyboard simulation.
    """

    TUI_COMMANDS = {
        "vim", "nvim", "nano", "emacs", "vi", "less", "more", "top", "htop",
        "btop", "man", "fzf", "lazygit", "lazydocker", "tig", "ranger",
        "mc", "ncdu", "nnn", "lf", "vifm", "tmux", "screen", "depviz"
    }

    def __init__(self, output: str = "output.gif", fps: int = 10, radius: int = 0,
                 typing_speed_ms: int = 50, config: TapeConfig | None = None):
        self.output = Path(output)
        self.fps = fps
        self.frame_duration = 1000 // fps
        self.typing_speed_ms = typing_speed_ms
        self.frames: list[Image.Image] = []
        self.frame_durations: list[int] = []
        self.bbox = None
        self.radius = radius
        self.last_valid_frame = None
        self.expected_size = None
        self.active_process = None
        self.config = config or TapeConfig()

    def start_capture(self):
        """Detect terminal window region."""
        if not HAS_CAPTURE:
            raise RuntimeError("Screen capture not available on this platform")

        region = get_terminal_window_rect()

        if region:
            x, y, w, h = region
            if w > 0 and h > 0:
                self.bbox = (x, y, x + w, y + h)
            else:
                self.bbox = None
        else:
            self.bbox = None

        return region

    def capture_frame(self) -> bool:
        """Capture current screen state."""
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

            if self.radius > 0:
                frame = apply_rounded_corners(frame, self.radius)

            self.last_valid_frame = frame.copy()
            self.frames.append(frame)
            self.frame_durations.append(self.frame_duration)
            return True
        except Exception:
            if self.last_valid_frame:
                self.frames.append(self.last_valid_frame.copy())
                self.frame_durations.append(self.frame_duration)
                return True
            return False

    def run_actions(self, actions: list[Action], typing_speed_ms: int = 50):
        """Run actions in the terminal and capture frames."""
        # Clear terminal
        if sys.platform == "win32":
            os.system("cls")
        else:
            os.system("clear")

        time.sleep(0.3)
        self.capture_frame()

        current_cmd = ""

        for action in actions:
            if isinstance(action, TypeAction):
                for char in action.text:
                    print(char, end="", flush=True)
                    time.sleep(typing_speed_ms / 1000)
                    self.capture_frame()
                current_cmd += action.text

            elif isinstance(action, EnterAction):
                print(flush=True)
                self.capture_frame()

                if current_cmd and not current_cmd.startswith("#"):
                    cmd_name = current_cmd.split()[0].lower() if current_cmd.split() else ""
                    is_tui = cmd_name in self.TUI_COMMANDS

                    if is_tui:
                        self._start_command(current_cmd)
                        time.sleep(0.5)
                        self._capture_frames_for_duration(500)
                    else:
                        os.system(current_cmd)

                time.sleep(0.1)
                self.capture_frame()
                current_cmd = ""

            elif isinstance(action, SleepAction):
                self._capture_frames_for_duration(action.duration_ms)

            elif isinstance(action, KeyAction):
                _reset_terminal_hwnd()
                _get_terminal_hwnd(force_refresh=True)
                focus_terminal()
                time.sleep(0.05)
                send_key(action.key)
                time.sleep(0.1)
                self.capture_frame()
                self._capture_frames_for_duration(150)

        self._capture_frames_for_duration(500)

    def _start_command(self, cmd: str) -> None:
        """Start a command without waiting for it to complete."""
        try:
            self._cleanup_process()
            env = os.environ.copy()

            if sys.platform == "win32":
                self.active_process = subprocess.Popen(
                    cmd,
                    shell=True,
                    env=env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )
            else:
                self.active_process = subprocess.Popen(
                    cmd,
                    shell=True,
                    env=env,
                    start_new_session=True,
                )
        except Exception:
            self.active_process = None

    def _cleanup_process(self) -> None:
        """Terminate any running process."""
        if self.active_process is not None:
            try:
                if self.active_process.poll() is None:
                    self.active_process.terminate()
                    try:
                        self.active_process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        self.active_process.kill()
            except Exception:
                pass
            finally:
                self.active_process = None

    def _capture_frames_for_duration(self, duration_ms: int) -> None:
        """Capture frames for a specified duration."""
        if duration_ms <= 0:
            return

        frames_needed = max(1, duration_ms // self.frame_duration)
        for _ in range(frames_needed):
            time.sleep(self.frame_duration / 1000)
            self.capture_frame()

    def save_gif(self) -> Path:
        """Save captured frames as GIF using ffmpeg or PIL."""
        if not self.frames:
            raise ValueError("No frames captured")

        from ..exporters import GifExporter

        exporter = GifExporter(self.frames, self.frame_durations, self.config)
        return exporter.export(self.output)


def record_terminal(script_path: Path, output: Path | None = None) -> Path:
    """Record by screen-capturing the actual terminal window.

    Args:
        script_path: Path to the script file
        output: Optional output path override

    Returns:
        Path to the created output file
    """
    if not HAS_CAPTURE:
        raise RuntimeError("Screen capture not available on this platform")

    from ..parser import parse_script

    config, actions = parse_script(script_path)

    # Determine output path
    if output:
        output_path = output
    elif config.output:
        clean_output = config.output.strip('"').strip("'")
        output_path = Path(clean_output)
    else:
        output_path = script_path.with_suffix(".gif")

    if not output_path.suffix:
        output_path = output_path.with_suffix(".gif")

    # Use outer radius for rounded corners
    outer_r = config.radius_outer if config.radius_outer is not None else config.radius

    recorder = TerminalRecorder(
        str(output_path),
        fps=config.fps,
        radius=outer_r,
        typing_speed_ms=config.typing_speed_ms,
        config=config,
    )

    region = recorder.start_capture()
    if region:
        w, h = region[2], region[3]
        if w < 100 or h < 100:
            raise RuntimeError(
                f"Window detection returned invalid size ({w}x{h}). "
                "Make sure your terminal window is visible and in focus."
            )
        print(f"[Capturing {w}x{h} window]")
    else:
        print("[Warning: Could not detect terminal window, capturing full screen]")

    recorder.run_actions(actions, config.typing_speed_ms)
    recorder.save_gif()

    return output_path
