"""Window detection utilities for terminal capture.

Provides cross-platform functions to detect terminal window bounds
for screen capture functionality.
"""
import subprocess

from .platform import is_windows, is_macos, is_linux


def get_terminal_window_rect() -> tuple[int, int, int, int] | None:
    """Get the terminal window's position and size.

    Returns:
        (x, y, width, height) tuple or None if detection fails.
    """
    if is_windows:
        return _get_window_rect_windows()
    elif is_macos:
        return _get_window_rect_macos()
    else:
        return _get_window_rect_linux()


def _get_window_rect_windows() -> tuple[int, int, int, int] | None:
    """Get terminal window rect on Windows using Win32 API."""
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        # Make process DPI aware for accurate coordinates
        try:
            # Windows 10 1607+ (Per-Monitor V2)
            user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except Exception:
            try:
                # Windows 8.1+ (Per-Monitor)
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
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

    return None


def _get_window_rect_macos() -> tuple[int, int, int, int] | None:
    """Get terminal window rect on macOS using AppleScript."""
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

    return None


def _get_window_rect_linux() -> tuple[int, int, int, int] | None:
    """Get terminal window rect on Linux using xdotool."""
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
