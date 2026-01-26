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
from .tape import TapeConfig, TypeAction, EnterAction, SleepAction, KeyAction


# =============================================================================
# KEYBOARD SIMULATION (for TUI interaction)
# =============================================================================

# Virtual key codes for Windows
_WIN_VK_CODES = {
    # Navigation
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
    # Editing
    "backspace": 0x08, "delete": 0x2E, "tab": 0x09, "space": 0x20,
    # Control
    "escape": 0x1B, "enter": 0x0D, "return": 0x0D,
    # Function keys
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    # Modifiers (used internally)
    "ctrl": 0x11, "alt": 0x12, "shift": 0x10,
}

# Key names for xdotool (Linux)
_XDOTOOL_KEYS = {
    "up": "Up", "down": "Down", "left": "Left", "right": "Right",
    "home": "Home", "end": "End", "pageup": "Page_Up", "pagedown": "Page_Down",
    "backspace": "BackSpace", "delete": "Delete", "tab": "Tab", "space": "space",
    "escape": "Escape", "enter": "Return", "return": "Return",
    "f1": "F1", "f2": "F2", "f3": "F3", "f4": "F4",
    "f5": "F5", "f6": "F6", "f7": "F7", "f8": "F8",
    "f9": "F9", "f10": "F10", "f11": "F11", "f12": "F12",
}

# Key codes for macOS (using key codes for System Events)
_MACOS_KEY_CODES = {
    "up": 126, "down": 125, "left": 123, "right": 124,
    "home": 115, "end": 119, "pageup": 116, "pagedown": 121,
    "backspace": 51, "delete": 117, "tab": 48, "space": 49,
    "escape": 53, "enter": 36, "return": 36,
    "f1": 122, "f2": 120, "f3": 99, "f4": 118,
    "f5": 96, "f6": 97, "f7": 98, "f8": 100,
    "f9": 101, "f10": 109, "f11": 103, "f12": 111,
}


def send_key(key: str) -> bool:
    """Send a keystroke to the active window.

    Args:
        key: Key name like "escape", "up", "ctrl+c", "alt+f4", etc.

    Returns:
        True if successful, False otherwise.
    """
    key = key.lower().strip()

    # Parse modifiers (ctrl+c, alt+f4, etc.)
    modifiers = []
    actual_key = key
    if "+" in key:
        parts = key.split("+")
        modifiers = [p.strip() for p in parts[:-1]]
        actual_key = parts[-1].strip()

    if sys.platform == "win32":
        return _send_key_windows(actual_key, modifiers)
    elif sys.platform == "darwin":
        return _send_key_macos(actual_key, modifiers)
    else:
        return _send_key_linux(actual_key, modifiers)


def _send_key_windows(key: str, modifiers: list[str]) -> bool:
    """Send keystroke on Windows using SendInput."""
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32

        # Constants
        INPUT_KEYBOARD = 1
        KEYEVENTF_KEYUP = 0x0002
        KEYEVENTF_SCANCODE = 0x0008

        # Properly define the INPUT structure with union (required for 64-bit)
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class HARDWAREINPUT(ctypes.Structure):
            _fields_ = [
                ("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD),
            ]

        class INPUT_UNION(ctypes.Union):
            _fields_ = [
                ("mi", MOUSEINPUT),
                ("ki", KEYBDINPUT),
                ("hi", HARDWAREINPUT),
            ]

        class INPUT(ctypes.Structure):
            _fields_ = [
                ("type", wintypes.DWORD),
                ("union", INPUT_UNION),
            ]

        # Set up SendInput function signature
        user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
        user32.SendInput.restype = wintypes.UINT

        def press_key(vk_code: int) -> None:
            inp = INPUT()
            inp.type = INPUT_KEYBOARD
            inp.union.ki.wVk = vk_code
            inp.union.ki.wScan = 0
            inp.union.ki.dwFlags = 0
            inp.union.ki.time = 0
            inp.union.ki.dwExtraInfo = None
            user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

        def release_key(vk_code: int) -> None:
            inp = INPUT()
            inp.type = INPUT_KEYBOARD
            inp.union.ki.wVk = vk_code
            inp.union.ki.wScan = 0
            inp.union.ki.dwFlags = KEYEVENTF_KEYUP
            inp.union.ki.time = 0
            inp.union.ki.dwExtraInfo = None
            user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

        # Get key code
        if key in _WIN_VK_CODES:
            vk_code = _WIN_VK_CODES[key]
        elif len(key) == 1:
            # Single character - get virtual key code
            vk_code = user32.VkKeyScanW(ord(key)) & 0xFF
        else:
            return False

        # Press modifiers
        for mod in modifiers:
            if mod in _WIN_VK_CODES:
                press_key(_WIN_VK_CODES[mod])
                time.sleep(0.01)

        # Press and release the key
        press_key(vk_code)
        time.sleep(0.02)
        release_key(vk_code)

        # Release modifiers (in reverse order)
        for mod in reversed(modifiers):
            if mod in _WIN_VK_CODES:
                time.sleep(0.01)
                release_key(_WIN_VK_CODES[mod])

        return True
    except Exception as e:
        return False


def _send_key_macos(key: str, modifiers: list[str]) -> bool:
    """Send keystroke on macOS using osascript (AppleScript)."""
    try:
        # Build modifier string for AppleScript
        mod_parts = []
        if "ctrl" in modifiers or "control" in modifiers:
            mod_parts.append("control down")
        if "alt" in modifiers or "option" in modifiers:
            mod_parts.append("option down")
        if "shift" in modifiers:
            mod_parts.append("shift down")
        if "cmd" in modifiers or "command" in modifiers:
            mod_parts.append("command down")

        mod_str = ""
        if mod_parts:
            mod_str = " using {" + ", ".join(mod_parts) + "}"

        # Get key code or use character
        if key in _MACOS_KEY_CODES:
            script = f'tell application "System Events" to key code {_MACOS_KEY_CODES[key]}{mod_str}'
        elif len(key) == 1:
            # Escape special characters for AppleScript string
            escaped_key = key.replace("\\", "\\\\").replace('"', '\\"')
            script = f'tell application "System Events" to keystroke "{escaped_key}"{mod_str}'
        else:
            return False

        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def _send_key_linux(key: str, modifiers: list[str]) -> bool:
    """Send keystroke on Linux using xdotool (X11) or ydotool (Wayland)."""
    # Build key combination
    key_combo = ""
    if "ctrl" in modifiers or "control" in modifiers:
        key_combo += "ctrl+"
    if "alt" in modifiers:
        key_combo += "alt+"
    if "shift" in modifiers:
        key_combo += "shift+"
    if "super" in modifiers or "meta" in modifiers:
        key_combo += "super+"

    # Get key name
    if key in _XDOTOOL_KEYS:
        key_name = _XDOTOOL_KEYS[key]
    elif len(key) == 1:
        key_name = key
    else:
        return False

    key_combo += key_name

    # Try xdotool first (X11)
    try:
        result = subprocess.run(
            ["xdotool", "key", key_combo],
            capture_output=True, timeout=5
        )
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        pass  # xdotool not installed, try ydotool
    except Exception:
        pass

    # Try ydotool (Wayland) - uses different key names
    try:
        # ydotool uses different syntax: ydotool key <keycode>
        # For simplicity, use type for characters and key for special keys
        ydotool_key = key_name.lower()
        result = subprocess.run(
            ["ydotool", "key", ydotool_key],
            capture_output=True, timeout=5
        )
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        pass  # ydotool not installed
    except Exception:
        pass

    # Try wtype (another Wayland option)
    try:
        if len(key) == 1 and not modifiers:
            result = subprocess.run(
                ["wtype", key],
                capture_output=True, timeout=5
            )
        else:
            # wtype uses -k for special keys, -M for modifiers
            cmd = ["wtype"]
            for mod in modifiers:
                cmd.extend(["-M", mod])
            cmd.extend(["-k", key_name])
            for mod in modifiers:
                cmd.extend(["-m", mod])  # release modifier
            result = subprocess.run(cmd, capture_output=True, timeout=5)
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        pass
    except Exception:
        pass

    return False


def type_text(text: str) -> bool:
    """Type text character by character.

    Args:
        text: The text to type.

    Returns:
        True if successful, False otherwise.
    """
    if sys.platform == "win32":
        return _type_text_windows(text)
    elif sys.platform == "darwin":
        return _type_text_macos(text)
    else:
        return _type_text_linux(text)


def _type_text_windows(text: str) -> bool:
    """Type text on Windows using SendInput."""
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32

        INPUT_KEYBOARD = 1
        KEYEVENTF_UNICODE = 0x0004
        KEYEVENTF_KEYUP = 0x0002

        # Properly define the INPUT structure with union (required for 64-bit)
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class HARDWAREINPUT(ctypes.Structure):
            _fields_ = [
                ("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD),
            ]

        class INPUT_UNION(ctypes.Union):
            _fields_ = [
                ("mi", MOUSEINPUT),
                ("ki", KEYBDINPUT),
                ("hi", HARDWAREINPUT),
            ]

        class INPUT(ctypes.Structure):
            _fields_ = [
                ("type", wintypes.DWORD),
                ("union", INPUT_UNION),
            ]

        # Set up SendInput function signature
        user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
        user32.SendInput.restype = wintypes.UINT

        for char in text:
            # Key down with Unicode
            inp_down = INPUT()
            inp_down.type = INPUT_KEYBOARD
            inp_down.union.ki.wVk = 0
            inp_down.union.ki.wScan = ord(char)
            inp_down.union.ki.dwFlags = KEYEVENTF_UNICODE
            inp_down.union.ki.time = 0
            inp_down.union.ki.dwExtraInfo = None

            # Key up with Unicode
            inp_up = INPUT()
            inp_up.type = INPUT_KEYBOARD
            inp_up.union.ki.wVk = 0
            inp_up.union.ki.wScan = ord(char)
            inp_up.union.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
            inp_up.union.ki.time = 0
            inp_up.union.ki.dwExtraInfo = None

            user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(INPUT))
            user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(INPUT))
            time.sleep(0.01)  # Small delay between characters

        return True
    except Exception:
        return False


def _type_text_macos(text: str) -> bool:
    """Type text on macOS using osascript (AppleScript)."""
    try:
        # Escape special characters for AppleScript string
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        script = f'tell application "System Events" to keystroke "{escaped}"'
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def _type_text_linux(text: str) -> bool:
    """Type text on Linux using xdotool (X11) or ydotool/wtype (Wayland)."""
    # Try xdotool first (X11)
    try:
        result = subprocess.run(
            ["xdotool", "type", "--", text],
            capture_output=True, timeout=10
        )
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        pass
    except Exception:
        pass

    # Try ydotool (Wayland)
    try:
        result = subprocess.run(
            ["ydotool", "type", "--", text],
            capture_output=True, timeout=10
        )
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        pass
    except Exception:
        pass

    # Try wtype (Wayland)
    try:
        result = subprocess.run(
            ["wtype", text],
            capture_output=True, timeout=10
        )
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        pass
    except Exception:
        pass

    return False


# Store terminal window handle for focus management
_terminal_hwnd = None


def _get_terminal_hwnd():
    """Get the terminal window handle (Windows only)."""
    global _terminal_hwnd
    if _terminal_hwnd is not None:
        return _terminal_hwnd

    if sys.platform != "win32":
        return None

    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        # Try to get the console window first
        kernel32.GetConsoleWindow.restype = wintypes.HWND
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            _terminal_hwnd = hwnd
            return hwnd

        # Fall back to foreground window
        user32.GetForegroundWindow.restype = wintypes.HWND
        hwnd = user32.GetForegroundWindow()
        _terminal_hwnd = hwnd
        return hwnd
    except Exception:
        return None


def focus_terminal():
    """Ensure the terminal window has keyboard focus.

    This is important for sending keystrokes to TUI applications.
    """
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32

            hwnd = _get_terminal_hwnd()
            if hwnd:
                # Bring window to foreground and set focus
                user32.SetForegroundWindow.argtypes = [wintypes.HWND]
                user32.SetForegroundWindow.restype = wintypes.BOOL
                user32.SetForegroundWindow(hwnd)

                user32.SetFocus.argtypes = [wintypes.HWND]
                user32.SetFocus.restype = wintypes.HWND
                user32.SetFocus(hwnd)

                time.sleep(0.05)  # Small delay to let focus settle
                return True
        except Exception:
            pass

    elif sys.platform == "darwin":
        # On macOS, the terminal should already have focus since we're running in it
        # But we can try to activate the frontmost app
        try:
            script = '''
            tell application "System Events"
                set frontApp to first application process whose frontmost is true
                set frontmost of frontApp to true
            end tell
            '''
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=2)
            return True
        except Exception:
            pass

    else:  # Linux
        # Try xdotool to focus the active window
        try:
            result = subprocess.run(
                ["xdotool", "getactivewindow", "windowfocus", "--sync"],
                capture_output=True, timeout=2
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass

    return False

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

            elif isinstance(action, KeyAction):
                # KeyAction is only meaningful in --terminal mode
                # In live mode, we just pause briefly to simulate the key press
                print(f"[Note: 'key \"{action.key}\"' requires --terminal mode for TUI interaction]")
                self.capture_frame(100)

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
    """Records the actual terminal window via screen capture.

    Supports TUI applications by using non-blocking command execution
    and keyboard simulation for interactive input.
    """

    def __init__(self, output: str = "output.gif", fps: int = 10, radius: int = 0,
                 typing_speed_ms: int = 50):
        self.output = Path(output)
        self.fps = fps
        self.frame_duration = 1000 // fps
        self.typing_speed_ms = typing_speed_ms
        self.frames: list[Image.Image] = []
        self.bbox = None  # (left, top, right, bottom) for ImageGrab
        self.radius = radius  # Corner radius for rounded corners
        self.last_valid_frame = None  # For alt-tab recovery
        self.expected_size = None  # Track expected frame size
        self.active_process = None  # Track running TUI process

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
        """Legacy method for backwards compatibility.

        commands: list of (command_string, sleep_after_ms)
        """
        # Convert to actions format
        actions = []
        for cmd, sleep_ms in commands:
            if cmd:
                actions.append(TypeAction(text=cmd))
                actions.append(EnterAction())
            if sleep_ms > 0:
                actions.append(SleepAction(ms=sleep_ms))

        self.run_actions(actions, typing_speed_ms)

    def run_actions(self, actions: list, typing_speed_ms: int = 50):
        """Run actions in the terminal and capture frames.

        Handles TypeAction, EnterAction, SleepAction, and KeyAction.
        Commands are executed non-blocking to support TUI applications.
        """
        # Store terminal handle for focus management (Windows)
        _get_terminal_hwnd()

        # Clear terminal for clean recording
        if sys.platform == "win32":
            os.system("cls")
        else:
            os.system("clear")

        time.sleep(0.3)
        self.capture_frame()

        current_cmd = ""  # Accumulate typed text for command execution

        for action in actions:
            # Ensure terminal has focus before any input
            focus_terminal()

            if isinstance(action, TypeAction):
                # Type text character by character using keyboard simulation
                for char in action.text:
                    type_text(char)
                    time.sleep(typing_speed_ms / 1000)
                    self.capture_frame()
                current_cmd += action.text

            elif isinstance(action, EnterAction):
                # Send enter key - the terminal shell will execute the typed command
                send_key("enter")
                time.sleep(0.1)
                self.capture_frame()

                # NOTE: We do NOT use subprocess to run the command!
                # The keyboard simulation already typed the command and pressed enter,
                # so the terminal shell will execute it naturally.
                # This is what allows TUI apps to work properly.

                current_cmd = ""  # Reset for next command

                # Give commands/TUI apps time to start and render
                time.sleep(0.3)
                self._capture_frames_for_duration(300)

            elif isinstance(action, SleepAction):
                # Capture frames during the sleep period
                self._capture_frames_for_duration(action.ms)

            elif isinstance(action, KeyAction):
                # Ensure focus and send special key (for TUI interaction)
                focus_terminal()
                time.sleep(0.05)
                send_key(action.key)
                time.sleep(0.1)
                self.capture_frame()

                # Give the TUI time to respond
                self._capture_frames_for_duration(150)

        # Final frames
        self._capture_frames_for_duration(500)

    def _start_command(self, cmd: str) -> None:
        """Start a command without waiting for it to complete.

        This allows TUI applications to run while we continue capturing frames.
        """
        try:
            # Clean up previous process if any
            self._cleanup_process()

            # Set environment for cleaner TUI output
            env = os.environ.copy()

            # Start process without waiting
            # Use shell=True to handle complex commands
            # Don't capture output - let it go to the terminal
            if sys.platform == "win32":
                # On Windows, use CREATE_NEW_PROCESS_GROUP to allow clean termination
                self.active_process = subprocess.Popen(
                    cmd,
                    shell=True,
                    env=env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )
            else:
                # On Unix, start in new process group
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
                # Check if still running
                if self.active_process.poll() is None:
                    # Try graceful termination first
                    self.active_process.terminate()
                    try:
                        self.active_process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        # Force kill if termination didn't work
                        self.active_process.kill()
            except Exception:
                pass
            finally:
                self.active_process = None

    def _capture_frames_for_duration(self, duration_ms: int) -> None:
        """Capture frames for a specified duration.

        This keeps capturing frames while TUI apps are running,
        ensuring we get smooth animation of their interface.
        """
        if duration_ms <= 0:
            return

        frames_needed = max(1, duration_ms // self.frame_duration)
        for _ in range(frames_needed):
            time.sleep(self.frame_duration / 1000)
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

    Supports TUI applications through:
    - Non-blocking command execution
    - Keyboard simulation for key actions
    - Continuous frame capture during sleeps
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

    # Initialize recorder with outer radius for rounded corners
    # For --terminal mode, only outer radius applies (we capture the actual window)
    outer_r = config.radius_outer if config.radius_outer is not None else config.radius
    recorder = TerminalRecorder(
        str(output_path),
        fps=config.fps,
        radius=outer_r,
        typing_speed_ms=config.typing_speed_ms,
    )

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

    # Run actions directly (supports TUI apps with key actions)
    recorder.run_actions(actions, config.typing_speed_ms)
    recorder.save_gif()

    return output_path
