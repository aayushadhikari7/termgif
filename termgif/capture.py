"""Terminal capture and live recording."""
import sys
import os
import time
import subprocess
from pathlib import Path
from PIL import Image, ImageGrab
import numpy as np
import cv2

from .renderer import TerminalRenderer, TerminalStyle
from .tape import TapeConfig, TypeAction, EnterAction, SleepAction

# Screen capture support - use PIL's ImageGrab (built-in, more reliable)
HAS_CAPTURE = True
try:
    # Test if ImageGrab works on this platform
    ImageGrab.grab(bbox=(0, 0, 1, 1))
except Exception:
    HAS_CAPTURE = False


# =============================================================================
# LIVE RECORDING (real commands + our renderer)
# =============================================================================

class LiveRecorder:
    """Records real command execution with our renderer."""

    def __init__(self, config: TapeConfig):
        self.config = config
        # Use specific radius if set, otherwise fall back to general radius
        inner_r = config.radius_inner if config.radius_inner is not None else config.radius
        outer_r = config.radius_outer if config.radius_outer is not None else config.radius
        style = TerminalStyle(
            width=config.width,
            height=config.height,
            font_size=config.font_size,
            title=config.title,
            scale=config.quality,
            chrome=config.chrome,
            theme=config.theme,
            padding=config.padding,
            prompt=config.prompt,
            cursor=config.cursor,
            corner_radius=inner_r,
            outer_radius=outer_r,
        )
        self.renderer = TerminalRenderer(style)
        self.frames: list[Image.Image] = []
        self.frame_durations: list[int] = []

    def capture_frame(self, duration_ms: int = 100) -> None:
        """Capture current terminal state as a frame."""
        frame = self.renderer.render()
        self.frames.append(frame)
        self.frame_durations.append(duration_ms)

    def execute_command(self, cmd: str) -> str:
        """Execute a real command and return output."""
        if not cmd or cmd.startswith("#"):
            return ""

        try:
            # Set environment to disable colors/progress for cleaner output
            env = os.environ.copy()
            env["NO_COLOR"] = "1"
            env["TERM"] = "dumb"
            env["CI"] = "1"  # Many tools simplify output in CI mode

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,  # Longer timeout for CLI tools
                cwd=Path.cwd(),
                env=env,
                encoding='utf-8',
                errors='replace',  # Handle special characters gracefully
            )
            output = result.stdout
            if result.stderr and result.returncode != 0:
                output += result.stderr
            return output.rstrip()
        except subprocess.TimeoutExpired:
            return "[Command timed out after 60s]"
        except Exception as e:
            return f"[Error: {e}]"

    def _add_output_animated(self, output: str) -> None:
        """Add output line by line with animation for smooth scrolling."""
        if not output:
            return

        lines = output.splitlines()
        max_width = self.renderer.style.width

        for line in lines:
            # Wrap long lines
            if len(line) > max_width:
                while len(line) > max_width:
                    self.renderer.state.lines.append(line[:max_width])
                    self.capture_frame(30)  # Fast scroll
                    line = line[max_width:]
                if line:
                    self.renderer.state.lines.append(line)
                    self.capture_frame(30)
            else:
                self.renderer.state.lines.append(line)
                self.capture_frame(30)  # 30ms per line = smooth scroll

        # Add blank line and restore prompt
        self.renderer.state.lines.append("")
        self.renderer.state.current_line = self.renderer.state.prompt
        self.capture_frame(100)

    def run_actions(self, actions: list) -> None:
        """Run all actions with real command execution."""
        self.capture_frame(self.config.start_delay)

        for action in actions:
            if isinstance(action, TypeAction):
                for char in action.text:
                    self.renderer.type_char(char)
                    self.capture_frame(self.config.typing_speed_ms)

            elif isinstance(action, EnterAction):
                cmd = self.renderer.press_enter()
                self.capture_frame(100)

                if cmd and not cmd.startswith("#"):
                    output = self.execute_command(cmd)
                    # Animate output line by line for smooth scrolling
                    self._add_output_animated(output)

            elif isinstance(action, SleepAction):
                self.capture_frame(action.ms)

        self.capture_frame(self.config.end_delay)

    def save_gif(self, output_path: Path) -> None:
        """Save frames as animated GIF."""
        if not self.frames:
            raise ValueError("No frames captured")

        self.frames[0].save(
            output_path,
            save_all=True,
            append_images=self.frames[1:],
            duration=self.frame_durations,
            loop=self.config.loop,
            optimize=True,
        )


def record_live(script_path: Path, output: Path | None = None) -> Path:
    """Record script with real command execution."""
    from .tg_parser import parse_tg
    from .tape import parse_tape

    suffix = script_path.suffix.lower()
    if suffix == ".tg":
        config, actions = parse_tg(script_path)
    else:
        config, actions = parse_tape(script_path)

    # Determine output path
    if output:
        output_path = output
    elif config.output:
        output_path = Path(config.output)
    else:
        # Default to script name with .gif extension
        output_path = script_path.with_suffix(".gif")

    # Ensure .gif extension
    if not output_path.suffix:
        output_path = output_path.with_suffix(".gif")

    recorder = LiveRecorder(config)
    recorder.run_actions(actions)
    recorder.save_gif(output_path)

    return output_path


# =============================================================================
# TERMINAL SCREEN CAPTURE (capture actual terminal window)
# =============================================================================

def get_terminal_window_rect():
    """Get the terminal window's position and size.

    Returns (x, y, width, height) or None.
    """
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            # Make process DPI aware for accurate coordinates
            try:
                # Windows 10 1607+ (Per-Monitor V2)
                user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))  # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
            except Exception:
                try:
                    # Windows 8.1+ (Per-Monitor)
                    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
                except Exception:
                    try:
                        # Windows Vista+ (System DPI aware)
                        user32.SetProcessDPIAware()
                    except Exception:
                        pass

            # Set up function signatures
            kernel32.GetConsoleWindow.restype = wintypes.HWND
            user32.GetForegroundWindow.restype = wintypes.HWND
            user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
            user32.GetWindowRect.restype = wintypes.BOOL

            # Function to get window rect from hwnd
            def get_rect(hwnd):
                if not hwnd:
                    return None

                # Try DwmGetWindowAttribute first (gets actual visible bounds without shadow)
                try:
                    dwmapi = ctypes.windll.dwmapi
                    DWMWA_EXTENDED_FRAME_BOUNDS = 9
                    rect = wintypes.RECT()
                    result = dwmapi.DwmGetWindowAttribute(
                        hwnd,
                        DWMWA_EXTENDED_FRAME_BOUNDS,
                        ctypes.byref(rect),
                        ctypes.sizeof(rect)
                    )
                    if result == 0:  # S_OK
                        x, y = rect.left, rect.top
                        w, h = rect.right - rect.left, rect.bottom - rect.top
                        # Add small inset to crop any remaining edge artifacts (1px each side)
                        inset = 1
                        x += inset
                        y += inset
                        w -= inset * 2
                        h -= inset * 2
                        if w > 0 and h > 0:
                            return (x, y, w, h)
                except Exception:
                    pass

                # Fallback to GetWindowRect
                rect = wintypes.RECT()
                if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                    x, y = rect.left, rect.top
                    w, h = rect.right - rect.left, rect.bottom - rect.top
                    # Handle maximized/off-screen windows
                    if x < 0:
                        w += x
                        x = 0
                    if y < 0:
                        h += y
                        y = 0
                    if w > 0 and h > 0:
                        return (x, y, w, h)
                return None

            # Strategy 1: GetConsoleWindow (works for cmd.exe, PowerShell legacy)
            hwnd = kernel32.GetConsoleWindow()
            if hwnd:
                result = get_rect(hwnd)
                if result:
                    return result

            # Strategy 2: Attach to parent console (for Windows Terminal, etc.)
            ATTACH_PARENT_PROCESS = 0xFFFFFFFF
            try:
                kernel32.FreeConsole()
                if kernel32.AttachConsole(ATTACH_PARENT_PROCESS):
                    hwnd = kernel32.GetConsoleWindow()
                    if hwnd:
                        result = get_rect(hwnd)
                        if result:
                            return result
            except Exception:
                pass

            # Strategy 3: Find parent process window
            try:
                kernel32.GetCurrentProcessId.restype = wintypes.DWORD

                # Get parent PID using NtQueryInformationProcess or snapshot
                import ctypes.wintypes as wt

                TH32CS_SNAPPROCESS = 0x00000002

                class PROCESSENTRY32(ctypes.Structure):
                    _fields_ = [
                        ("dwSize", wt.DWORD),
                        ("cntUsage", wt.DWORD),
                        ("th32ProcessID", wt.DWORD),
                        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                        ("th32ModuleID", wt.DWORD),
                        ("cntThreads", wt.DWORD),
                        ("th32ParentProcessID", wt.DWORD),
                        ("pcPriClassBase", ctypes.c_long),
                        ("dwFlags", wt.DWORD),
                        ("szExeFile", ctypes.c_char * 260),
                    ]

                kernel32.CreateToolhelp32Snapshot.restype = wt.HANDLE
                kernel32.Process32First.argtypes = [wt.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
                kernel32.Process32Next.argtypes = [wt.HANDLE, ctypes.POINTER(PROCESSENTRY32)]

                current_pid = kernel32.GetCurrentProcessId()
                snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)

                if snapshot:
                    pe = PROCESSENTRY32()
                    pe.dwSize = ctypes.sizeof(PROCESSENTRY32)

                    parent_pid = None
                    if kernel32.Process32First(snapshot, ctypes.byref(pe)):
                        while True:
                            if pe.th32ProcessID == current_pid:
                                parent_pid = pe.th32ParentProcessID
                                break
                            if not kernel32.Process32Next(snapshot, ctypes.byref(pe)):
                                break

                    kernel32.CloseHandle(snapshot)

                    if parent_pid:
                        # Find windows belonging to parent process
                        user32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
                        user32.GetWindowThreadProcessId.restype = wt.DWORD
                        user32.IsWindowVisible.argtypes = [wt.HWND]
                        user32.IsWindowVisible.restype = wt.BOOL

                        found_hwnd = None

                        @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
                        def enum_callback(hwnd, lparam):
                            nonlocal found_hwnd
                            pid = wt.DWORD()
                            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                            if pid.value == parent_pid and user32.IsWindowVisible(hwnd):
                                found_hwnd = hwnd
                                return False  # Stop enumeration
                            return True

                        user32.EnumWindows(enum_callback, 0)

                        if found_hwnd:
                            result = get_rect(found_hwnd)
                            if result:
                                return result
            except Exception:
                pass

            # Strategy 4: Foreground window (last resort - might not be the terminal)
            hwnd = user32.GetForegroundWindow()
            if hwnd:
                result = get_rect(hwnd)
                if result:
                    return result

        except Exception:
            pass

    elif sys.platform == "darwin":
        try:
            script = '''
            tell application "System Events"
                set frontApp to first application process whose frontmost is true
                set frontWindow to first window of frontApp
                set {x, y} to position of frontWindow
                set {w, h} to size of frontWindow
                return (x as text) & "," & (y as text) & "," & (w as text) & "," & (h as text)
            end tell
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(",")
                if len(parts) == 4:
                    return tuple(int(p) for p in parts)
        except Exception:
            pass

    else:  # Linux
        try:
            result = subprocess.run(
                ["xdotool", "getactivewindow", "getwindowgeometry", "--shell"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                vals = {}
                for line in result.stdout.strip().split("\n"):
                    if "=" in line:
                        k, v = line.split("=")
                        vals[k] = int(v)
                if all(k in vals for k in ["X", "Y", "WIDTH", "HEIGHT"]):
                    return (vals["X"], vals["Y"], vals["WIDTH"], vals["HEIGHT"])
        except Exception:
            pass

    return None


def apply_rounded_corners(frame: Image.Image, radius: int, bg_color: tuple = (30, 30, 46)) -> Image.Image:
    """Apply rounded corners to a frame.

    Since GIF doesn't support true alpha transparency, we render the corners
    with a solid background color (default: dark theme background).

    Args:
        frame: The frame to apply rounded corners to
        radius: Corner radius in pixels
        bg_color: RGB background color for corners (default: mocha theme bg)

    Returns RGB image with rounded corners.
    """
    if radius <= 0:
        return frame

    w, h = frame.size

    # Clamp radius to half of smallest dimension
    radius = min(radius, w // 2, h // 2)
    if radius <= 0:
        return frame

    # Ensure frame is RGB
    if frame.mode != "RGB":
        frame = frame.convert("RGB")

    from PIL import ImageDraw

    # Create rounded rectangle mask (white = keep, black = replace with bg)
    mask = Image.new("L", (w, h), 255)
    mask_draw = ImageDraw.Draw(mask)

    # Draw black corners (will be filled with background color)
    # Top-left corner
    mask_draw.rectangle([0, 0, radius, radius], fill=0)
    mask_draw.ellipse([0, 0, radius * 2, radius * 2], fill=255)

    # Top-right corner
    mask_draw.rectangle([w - radius, 0, w, radius], fill=0)
    mask_draw.ellipse([w - radius * 2, 0, w, radius * 2], fill=255)

    # Bottom-left corner
    mask_draw.rectangle([0, h - radius, radius, h], fill=0)
    mask_draw.ellipse([0, h - radius * 2, radius * 2, h], fill=255)

    # Bottom-right corner
    mask_draw.rectangle([w - radius, h - radius, w, h], fill=0)
    mask_draw.ellipse([w - radius * 2, h - radius * 2, w, h], fill=255)

    # Create background image
    bg = Image.new("RGB", (w, h), bg_color)

    # Composite: background where mask is black, frame where mask is white
    result = Image.composite(frame, bg, mask)

    return result


class TerminalRecorder:
    """Records the actual terminal window via screen capture."""

    def __init__(self, output: str = "output.gif", fps: int = 10, radius: int = 0):
        self.output = Path(output)
        self.fps = fps
        self.frame_duration = 1000 // fps
        self.frames: list[Image.Image] = []
        self.bbox = None  # (left, top, right, bottom) for ImageGrab
        self.radius = radius  # Corner radius for rounded corners
        self.last_valid_frame = None  # For alt-tab recovery
        self.expected_size = None  # Track expected frame size

    def start_capture(self):
        """Detect terminal window region."""
        if not HAS_CAPTURE:
            raise RuntimeError("Screen capture not available on this platform")

        # Detect the terminal window
        region = get_terminal_window_rect()

        if region:
            x, y, w, h = region
            # Validate dimensions
            if w > 0 and h > 0:
                self.bbox = (x, y, x + w, y + h)
            else:
                self.bbox = None  # Fallback to full screen
        else:
            self.bbox = None  # Fallback to full screen

        return region

    def capture_frame(self) -> bool:
        """Capture current screen state using PIL ImageGrab.

        Includes alt-tab recovery: if frame size changes unexpectedly,
        we use the last valid frame to avoid capturing other windows.
        """
        try:
            # ImageGrab.grab(bbox) - bbox is (left, top, right, bottom)
            frame = ImageGrab.grab(bbox=self.bbox)

            # Skip empty frames
            if frame.size[0] == 0 or frame.size[1] == 0:
                # Use last valid frame if available
                if self.last_valid_frame:
                    self.frames.append(self.last_valid_frame.copy())
                    return True
                return False

            # Convert to RGB and copy to avoid PIL internal state issues
            if frame.mode != "RGB":
                frame = frame.convert("RGB")
            frame = frame.copy()

            # Track expected size from first frame
            if self.expected_size is None:
                self.expected_size = frame.size

            # Alt-tab detection: if frame size changed, window probably switched
            # Use last valid frame to avoid capturing other windows
            if frame.size != self.expected_size:
                if self.last_valid_frame:
                    self.frames.append(self.last_valid_frame.copy())
                    return True
                # If no last frame, try to resize (should rarely happen)
                frame = frame.resize(self.expected_size, Image.Resampling.LANCZOS)

            # Apply rounded corners if configured (renders on solid bg color)
            if self.radius > 0:
                frame = apply_rounded_corners(frame, self.radius)

            # Store as last valid frame (always RGB now)
            self.last_valid_frame = frame.copy()

            self.frames.append(frame)
            return True
        except Exception:
            # On error, use last valid frame if available
            if self.last_valid_frame:
                self.frames.append(self.last_valid_frame.copy())
                return True
            return False

    def run_script(self, commands: list[tuple[str, int]], typing_speed_ms: int = 50):
        """Run commands in the terminal and capture frames.

        commands: list of (command_string, sleep_after_ms)
        """
        # Clear terminal for clean recording
        if sys.platform == "win32":
            os.system("cls")
        else:
            os.system("clear")

        time.sleep(0.3)
        self.capture_frame()

        for cmd, sleep_ms in commands:
            # Type the command character by character
            for char in cmd:
                print(char, end="", flush=True)
                time.sleep(typing_speed_ms / 1000)
                self.capture_frame()

            # Press enter
            print()
            self.capture_frame()

            # Execute command
            if cmd and not cmd.startswith("#"):
                os.system(cmd)

            time.sleep(0.1)
            self.capture_frame()

            # Wait and capture frames during sleep
            if sleep_ms > 0:
                frames_needed = max(1, sleep_ms // self.frame_duration)
                for _ in range(frames_needed):
                    time.sleep(self.frame_duration / 1000)
                    self.capture_frame()

        # Final frame
        time.sleep(0.5)
        self.capture_frame()

    def save_gif(self):
        """Save captured frames as GIF using ffmpeg."""
        import tempfile
        import shutil

        if not self.frames:
            raise ValueError("No frames captured")

        # Check ffmpeg availability
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("ffmpeg not found. Please install ffmpeg and add it to PATH.")

        if len(self.frames) == 0:
            raise ValueError("No frames were captured")

        # Get consistent size from first frame
        first_frame = self.frames[0]

        # Get target dimensions from PIL size (more reliable)
        target_w, target_h = first_frame.size

        # Create temp directory for frames
        temp_dir = tempfile.mkdtemp(prefix="termgif_")

        try:
            # Save frames as PNGs using OpenCV (much more reliable than PIL)
            saved_count = 0

            for i, frame in enumerate(self.frames):
                try:
                    if frame is None:
                        continue

                    # Ensure we have RGB data
                    if frame.mode != "RGB":
                        frame = frame.convert("RGB")

                    # Get dimensions and convert to numpy
                    w, h = frame.size
                    raw_data = frame.tobytes()
                    arr = np.frombuffer(raw_data, dtype=np.uint8).reshape((h, w, 3))

                    # Skip empty frames
                    if arr.size == 0:
                        continue

                    # Convert RGB to BGR for OpenCV
                    arr = arr[:, :, ::-1]
                    arr = np.ascontiguousarray(arr, dtype=np.uint8)

                    # Resize if needed for consistency
                    if arr.shape[0] != target_h or arr.shape[1] != target_w:
                        arr = cv2.resize(arr, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)

                    # Save as PNG using OpenCV
                    frame_path = os.path.join(temp_dir, f"frame_{saved_count:05d}.png")
                    if cv2.imwrite(frame_path, arr):
                        saved_count += 1

                except Exception:
                    continue

            if saved_count == 0:
                raise ValueError("No valid frames could be saved")

            # Calculate fps (avoid division by zero)
            fps = max(1, 1000 / max(1, self.frame_duration))

            # Build ffmpeg command
            input_pattern = os.path.join(temp_dir, "frame_%05d.png")
            output_path = str(self.output)

            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", input_pattern,
                "-vf", "split[s0][s1];[s0]palettegen=max_colors=256[p];[s1][p]paletteuse=dither=bayer",
                "-loop", "0",
                output_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                raise RuntimeError(f"ffmpeg failed: {error_msg}")

        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

        return self.output


def record_terminal(script_path: Path, output: Path | None = None) -> Path:
    """Record by screen-capturing the actual terminal window.

    This captures YOUR terminal (wezterm, ghostty, Windows Terminal, etc.)
    with all your custom themes and fonts.
    """
    if not HAS_CAPTURE:
        raise RuntimeError("Screen capture not available on this platform")

    from .tg_parser import parse_tg
    from .tape import parse_tape

    suffix = script_path.suffix.lower()
    if suffix == ".tg":
        config, actions = parse_tg(script_path)
    else:
        config, actions = parse_tape(script_path)

    # Determine output path with fallbacks
    if output:
        output_path = output
    elif config.output:
        # Strip any stray quotes from config (in case of parsing issues)
        clean_output = config.output.strip('"').strip("'")
        output_path = Path(clean_output)
    else:
        # Default to script name with .gif extension
        output_path = script_path.with_suffix(".gif")

    # Ensure .gif extension
    if not output_path.suffix:
        output_path = output_path.with_suffix(".gif")

    # Convert actions to commands
    commands = []
    current_cmd = ""
    current_sleep = 0

    for action in actions:
        if isinstance(action, TypeAction):
            current_cmd += action.text
        elif isinstance(action, EnterAction):
            commands.append((current_cmd, current_sleep))
            current_cmd = ""
            current_sleep = 0
        elif isinstance(action, SleepAction):
            current_sleep = action.ms

    # Initialize recorder with outer radius for rounded corners
    # For --terminal mode, only outer radius applies (we capture the actual window)
    outer_r = config.radius_outer if config.radius_outer is not None else config.radius
    recorder = TerminalRecorder(str(output_path), fps=config.fps, radius=outer_r)

    # Detect terminal window and start capture
    region = recorder.start_capture()
    if region:
        w, h = region[2], region[3]
        # Validate minimum size - if too small, window detection failed
        if w < 100 or h < 100:
            raise RuntimeError(
                f"Window detection returned invalid size ({w}x{h}). "
                "Make sure your terminal window is visible and in focus. "
                "Try clicking on your terminal before running this command."
            )
        print(f"[Capturing {w}x{h} window]")
    else:
        print("[Warning: Could not detect terminal window, capturing full screen]")

    # Run the script (will clear screen and record)
    recorder.run_script(commands, config.typing_speed_ms)
    recorder.save_gif()

    return output_path
