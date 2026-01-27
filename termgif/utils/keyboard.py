"""Cross-platform keyboard simulation utilities.

Provides functions to simulate keyboard input for TUI interaction.
Supports Windows (SendInput), macOS (AppleScript), and Linux (xdotool/ydotool/wtype).
"""
import sys
import time
import subprocess

from .platform import is_windows, is_macos, is_linux


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

    if is_windows:
        return _send_key_windows(actual_key, modifiers)
    elif is_macos:
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
    except Exception:
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
    if is_windows:
        return _type_text_windows(text)
    elif is_macos:
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


def _find_terminal_hwnd():
    """Find the terminal window handle using multiple strategies (Windows only)."""
    if not is_windows:
        return None

    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        # Strategy 1: GetConsoleWindow (works for cmd.exe, PowerShell legacy)
        kernel32.GetConsoleWindow.restype = wintypes.HWND
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            return hwnd

        # Strategy 2: Find parent process window (for Windows Terminal, etc.)
        try:
            kernel32.GetCurrentProcessId.restype = wintypes.DWORD
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
                        return found_hwnd
        except Exception:
            pass

        # Strategy 3: Foreground window (last resort)
        user32.GetForegroundWindow.restype = wintypes.HWND
        hwnd = user32.GetForegroundWindow()
        return hwnd

    except Exception:
        return None


def _get_terminal_hwnd(force_refresh: bool = False):
    """Get the terminal window handle (Windows only).

    Args:
        force_refresh: If True, re-detect the window instead of using cached value.
    """
    global _terminal_hwnd
    if _terminal_hwnd is not None and not force_refresh:
        return _terminal_hwnd

    _terminal_hwnd = _find_terminal_hwnd()
    return _terminal_hwnd


def _reset_terminal_hwnd():
    """Reset the cached terminal window handle."""
    global _terminal_hwnd
    _terminal_hwnd = None


def focus_terminal():
    """Ensure the terminal window has keyboard focus.

    This is important for sending keystrokes to TUI applications.
    """
    if is_windows:
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

    elif is_macos:
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
