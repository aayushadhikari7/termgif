"""PTY runner for executing commands with terminal emulation."""
import sys
import os
import subprocess
import threading
import time

from .emulator import TerminalEmulator, Cell

# Check for PTY support
HAS_PTY = False
HAS_CONPTY = False
HAS_WINPTY = False

if sys.platform == "win32":
    # Windows - use pywinpty for reliable TUI capture
    try:
        import winpty
        HAS_WINPTY = True
        HAS_CONPTY = True
        HAS_PTY = True
    except ImportError:
        pass  # No PTY support without pywinpty on Windows
else:
    # Unix - use native pty module
    try:
        import pty
        import select
        import fcntl
        import termios
        import struct
        HAS_PTY = True
    except ImportError:
        pass


class PTYRunner:
    """Runs commands in a pseudo-terminal and captures output.

    On Unix: Uses native PTY for full TUI support
    On Windows: Uses pywinpty (requires `pip install pywinpty`)
    """

    def __init__(self, width: int = 80, height: int = 24):
        self.width = width
        self.height = height
        self.emulator = TerminalEmulator(width=width, height=height)
        self.process = None
        self.master_fd = None
        self.running = False
        self._output_thread = None
        self._output_buffer = ""
        self._lock = threading.Lock()

    def start(self, cmd: str) -> bool:
        """Start a command in the PTY. Returns True if started successfully."""
        if sys.platform == "win32":
            if HAS_WINPTY:
                return self._start_winpty(cmd)
            else:
                return self._start_windows_fallback(cmd)
        elif HAS_PTY:
            return self._start_unix(cmd)
        return False

    def _start_winpty(self, cmd: str) -> bool:
        """Start command using pywinpty (Windows)."""
        try:
            import winpty

            self._winpty = winpty.PTY(self.width, self.height)
            self._winpty.spawn('cmd.exe')
            self.running = True

            # Start background reader
            self._output_thread = threading.Thread(target=self._read_output_winpty, daemon=True)
            self._output_thread.start()

            # Wait for shell prompt
            for _ in range(100):
                time.sleep(0.1)
                try:
                    data = self._winpty.read(blocking=False)
                    if data:
                        with self._lock:
                            self._output_buffer += data
                            self.emulator.feed(data)
                        if '>' in data:
                            break
                except Exception:
                    pass

            # Send command
            self._winpty.write(cmd + '\r\n')
            return True

        except Exception as e:
            print(f"[WinPTY Error: {e}]")
            return False

    def _read_output_winpty(self):
        """Read output from pywinpty."""
        while self.running:
            try:
                if not hasattr(self, '_winpty') or not self._winpty:
                    break
                data = self._winpty.read(blocking=False)
                if data:
                    with self._lock:
                        self._output_buffer += data
                        self.emulator.feed(data)
                else:
                    time.sleep(0.05)
            except Exception:
                time.sleep(0.05)
        self.running = False

    def _start_windows_fallback(self, cmd: str) -> bool:
        """Start command on Windows without PTY (limited TUI support)."""
        try:
            self.process = subprocess.Popen(
                cmd,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            self.running = True
            self._output_thread = threading.Thread(target=self._read_output_subprocess, daemon=True)
            self._output_thread.start()
            return True
        except Exception as e:
            print(f"[Process Error: {e}]")
            return False

    def _start_unix(self, cmd: str) -> bool:
        """Start command with Unix PTY."""
        try:
            self.master_fd, slave_fd = pty.openpty()

            # Set terminal size
            winsize = struct.pack('HHHH', self.height, self.width, 0, 0)
            fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, winsize)

            self.process = subprocess.Popen(
                cmd,
                shell=True,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                close_fds=True,
            )
            os.close(slave_fd)

            # Set master to non-blocking
            flags = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
            fcntl.fcntl(self.master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

            self.running = True
            self._output_thread = threading.Thread(target=self._read_output_unix, daemon=True)
            self._output_thread.start()
            return True
        except Exception as e:
            print(f"[PTY Error: {e}]")
            return False

    def _read_output_unix(self):
        """Read output from Unix PTY."""
        while self.running and self.master_fd is not None:
            try:
                ready, _, _ = select.select([self.master_fd], [], [], 0.05)
                if ready:
                    try:
                        data = os.read(self.master_fd, 4096)
                        if data:
                            text = data.decode('utf-8', errors='replace')
                            with self._lock:
                                self._output_buffer += text
                                self.emulator.feed(text)
                    except OSError:
                        break
            except Exception:
                break
        self.running = False

    def _read_output_subprocess(self):
        """Read output from subprocess (Windows fallback)."""
        while self.running and self.process and self.process.stdout:
            try:
                data = self.process.stdout.read(1)
                if data:
                    text = data.decode('utf-8', errors='replace')
                    with self._lock:
                        self._output_buffer += text
                        self.emulator.feed(text)
                elif self.process.poll() is not None:
                    break
            except Exception:
                break
        self.running = False

    def send_input(self, text: str):
        """Send text input to the running process."""
        if not self.running:
            return

        # WinPTY
        if hasattr(self, '_winpty') and self._winpty:
            try:
                self._winpty.write(text)
            except Exception:
                pass
            return

        data = text.encode('utf-8')

        # Unix PTY
        if self.master_fd is not None:
            try:
                os.write(self.master_fd, data)
            except Exception:
                pass
        # Subprocess fallback
        elif self.process and self.process.stdin:
            try:
                self.process.stdin.write(data)
                self.process.stdin.flush()
            except Exception:
                pass

    def send_key(self, key: str):
        """Send a special key to the process."""
        key_sequences = {
            "up": "\x1b[A", "down": "\x1b[B", "right": "\x1b[C", "left": "\x1b[D",
            "home": "\x1b[H", "end": "\x1b[F", "pageup": "\x1b[5~", "pagedown": "\x1b[6~",
            "insert": "\x1b[2~", "delete": "\x1b[3~",
            "enter": "\r", "return": "\r", "tab": "\t", "backspace": "\x7f",
            "escape": "\x1b", "space": " ",
            "f1": "\x1bOP", "f2": "\x1bOQ", "f3": "\x1bOR", "f4": "\x1bOS",
            "f5": "\x1b[15~", "f6": "\x1b[17~", "f7": "\x1b[18~", "f8": "\x1b[19~",
            "f9": "\x1b[20~", "f10": "\x1b[21~", "f11": "\x1b[23~", "f12": "\x1b[24~",
        }

        key_lower = key.lower()

        # Handle modifier combinations (ctrl+c, alt+x, etc.)
        if "+" in key_lower:
            parts = key_lower.split("+")
            modifiers, base_key = parts[:-1], parts[-1]

            if "ctrl" in modifiers or "control" in modifiers:
                if len(base_key) == 1 and base_key.isalpha():
                    self.send_input(chr(ord(base_key.upper()) - ord('A') + 1))
                    return

            if "alt" in modifiers:
                seq = key_sequences.get(base_key, base_key if len(base_key) == 1 else "")
                if seq:
                    self.send_input("\x1b" + seq)
                return

        # Simple key
        if key_lower in key_sequences:
            self.send_input(key_sequences[key_lower])
        elif len(key_lower) == 1:
            self.send_input(key_lower)

    def get_screen(self) -> list[list[Cell]]:
        """Get current screen state."""
        with self._lock:
            return self.emulator.get_screen()

    def get_lines(self) -> list[str]:
        """Get current screen as text lines."""
        with self._lock:
            return self.emulator.get_lines()

    def get_output_buffer(self) -> str:
        """Get raw output buffer."""
        with self._lock:
            return self._output_buffer

    def has_content(self) -> bool:
        """Check if there's any content in the screen."""
        with self._lock:
            return any(line.strip() for line in self.emulator.get_lines())

    def is_running(self) -> bool:
        """Check if the process is still running."""
        if hasattr(self, '_winpty') and self._winpty:
            try:
                return self._winpty.isalive()
            except Exception:
                return False
        if self.process:
            return self.process.poll() is None
        return self.running

    def wait(self, timeout: float = None) -> int | None:
        """Wait for process to complete. Returns exit code or None if timeout."""
        if self.process:
            try:
                return self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                return None
        return None

    def stop(self):
        """Stop the running process."""
        self.running = False

        # Stop WinPTY
        if hasattr(self, '_winpty') and self._winpty:
            try:
                self._winpty.write('exit\r\n')
                time.sleep(0.1)
            except Exception:
                pass
            self._winpty = None

        # Stop subprocess
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=1)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None

        # Close Unix PTY
        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except Exception:
                pass
            self.master_fd = None

    def __del__(self):
        """Cleanup on deletion."""
        self.stop()


def run_with_pty(cmd: str, width: int = 80, height: int = 24,
                 timeout: float = 10) -> tuple[list[str], int]:
    """Run a command with PTY and return final screen state."""
    runner = PTYRunner(width, height)
    if not runner.start(cmd):
        return [f"[Failed to start: {cmd}]"], 1
    exit_code = runner.wait(timeout=timeout)
    lines = runner.get_lines()
    runner.stop()
    return lines, exit_code if exit_code is not None else -1
