"""Platform detection utilities."""
import sys

# Platform flags
is_windows = sys.platform == "win32"
is_macos = sys.platform == "darwin"
is_linux = sys.platform.startswith("linux")


def get_platform() -> str:
    """Get the current platform name.

    Returns:
        'windows', 'macos', or 'linux'
    """
    if is_windows:
        return "windows"
    elif is_macos:
        return "macos"
    else:
        return "linux"
