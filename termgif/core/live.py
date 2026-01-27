"""Live recorder - executes real commands with PTY support."""
import os
import subprocess
import time
from pathlib import Path
from PIL import Image

from .recorder import BaseRecorder
from ..config import TapeConfig
from ..actions import Action, TypeAction, EnterAction, SleepAction, KeyAction
from ..renderer import StyledCell


class LiveRecorder(BaseRecorder):
    """Records real command execution with the custom renderer.

    Supports both regular commands (via subprocess) and TUI apps (via PTY).
    """

    # Known TUI/interactive commands that need PTY
    TUI_COMMANDS = {
        "vim", "nvim", "nano", "emacs", "vi", "less", "more", "top", "htop",
        "btop", "man", "fzf", "lazygit", "lazydocker", "tig", "ranger",
        "mc", "ncdu", "nnn", "lf", "vifm", "tmux", "screen", "depviz"
    }

    def __init__(self, config: TapeConfig):
        super().__init__(config)

        # PTY runner for TUI apps
        self.pty_runner = None

        # Native colors mode - preserve TUI app's colors
        self.native_colors = config.native_colors

    def _is_tui_command(self, cmd: str) -> bool:
        """Check if command is a known TUI app."""
        cmd_name = cmd.split()[0].lower() if cmd.split() else ""
        return cmd_name in self.TUI_COMMANDS

    def _render_pty_screen(self) -> None:
        """Render PTY screen state to our renderer."""
        if not self.pty_runner:
            return

        # Get screen from PTY emulator
        screen = self.pty_runner.get_screen()

        # Clear renderer and add PTY screen lines
        self.renderer.state.lines = []

        if self.native_colors:
            # Native color mode - preserve TUI app's colors
            styled_lines = []
            for row in screen:
                styled_row = []
                for cell in row:
                    styled_row.append(StyledCell(
                        char=cell.char,
                        fg=cell.fg,
                        bg=cell.bg,
                        bold=cell.bold,
                    ))
                styled_lines.append(styled_row)
            self.renderer.state.styled_lines = styled_lines
            # Also set text lines for fallback/cursor positioning
            for row in screen:
                line = ''.join(cell.char for cell in row).rstrip()
                self.renderer.state.lines.append(line)
        else:
            # Normal mode - extract plain text only
            self.renderer.state.styled_lines = None
            for row in screen:
                line = ''.join(cell.char for cell in row).rstrip()
                self.renderer.state.lines.append(line)

        # Don't show prompt in TUI mode
        self.renderer.state.current_line = ""

    def _wait_for_pty_content(self, timeout_ms: int = 2000, interval_ms: int = 50) -> bool:
        """Wait for PTY to have actual visible content."""
        if not self.pty_runner:
            return False

        import re

        elapsed = 0
        while elapsed < timeout_ms:
            # Check if emulator has any non-empty visible content
            if self.pty_runner.has_content():
                return True

            # Check raw output buffer for visible characters
            raw = self.pty_runner.get_output_buffer()
            if raw:
                # Remove ANSI escape sequences
                clean = re.sub(r'\x1b\[[^a-zA-Z]*[a-zA-Z]', '', raw)
                clean = re.sub(r'\x1b[^[]', '', clean)
                # Remove other control characters
                visible = ''.join(c for c in clean if c.isprintable() or c in '\n\r\t')
                if len(visible.strip()) > 5:  # Need actual visible content
                    return True

            time.sleep(interval_ms / 1000)
            elapsed += interval_ms

        return False

    def _capture_pty_frames(self, duration_ms: int, interval_ms: int = 100) -> None:
        """Capture frames from PTY during a duration."""
        frames_needed = max(1, duration_ms // interval_ms)
        for _ in range(frames_needed):
            time.sleep(interval_ms / 1000)
            self._render_pty_screen()
            self.capture_frame(interval_ms)

    def start_tui(self, cmd: str) -> bool:
        """Start a TUI app in PTY."""
        from ..pty import PTYRunner, HAS_PTY

        if not HAS_PTY:
            return False

        self.pty_runner = PTYRunner(
            width=self.config.width,
            height=self.config.height
        )
        return self.pty_runner.start(cmd)

    def stop_tui(self) -> None:
        """Stop running TUI app."""
        if self.pty_runner:
            self.pty_runner.stop()
            self.pty_runner = None

    def send_tui_key(self, key: str) -> None:
        """Send key to TUI app."""
        if self.pty_runner:
            self.pty_runner.send_key(key)

    def send_tui_text(self, text: str) -> None:
        """Send text to TUI app."""
        if self.pty_runner:
            self.pty_runner.send_input(text)

    def execute_command(self, cmd: str) -> str:
        """Execute a regular (non-TUI) command and return output."""
        if not cmd or cmd.startswith("#"):
            return ""

        try:
            # Set environment to disable colors/progress for cleaner output
            env = os.environ.copy()
            env["NO_COLOR"] = "1"
            env["TERM"] = "dumb"
            env["CI"] = "1"

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=Path.cwd(),
                env=env,
                encoding='utf-8',
                errors='replace',
            )
            output = result.stdout
            if result.stderr and result.returncode != 0:
                output += result.stderr
            return output.rstrip()
        except subprocess.TimeoutExpired:
            return "[Command timed out]"
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
                self.capture_frame(30)

        # Add blank line and restore prompt
        self.renderer.state.lines.append("")
        self.renderer.state.current_line = self.renderer.state.prompt
        self.capture_frame(100)

    def run_actions(self, actions: list[Action]) -> None:
        """Run all actions with real command execution."""
        from ..pty import HAS_PTY

        self.capture_frame(self.config.start_delay)

        in_tui_mode = False
        current_cmd = ""

        for action in actions:
            if isinstance(action, TypeAction):
                if in_tui_mode:
                    # In TUI mode, send text to PTY
                    for char in action.text:
                        self.send_tui_text(char)
                        time.sleep(self.config.typing_speed_ms / 1000)
                        self._render_pty_screen()
                        self.capture_frame(self.config.typing_speed_ms)
                else:
                    # Normal mode - render typing
                    for char in action.text:
                        self.renderer.type_char(char)
                        self.capture_frame(self.config.typing_speed_ms)
                    current_cmd += action.text

            elif isinstance(action, EnterAction):
                if in_tui_mode:
                    # In TUI mode, send enter to PTY
                    self.send_tui_key("enter")
                    time.sleep(0.1)
                    self._render_pty_screen()
                    self.capture_frame(100)
                else:
                    # Check if this command is a TUI app
                    cmd = self.renderer.press_enter()
                    self.capture_frame(100)

                    if cmd and not cmd.startswith("#"):
                        is_tui = self._is_tui_command(cmd)
                        if is_tui:
                            if not HAS_PTY:
                                # Show helpful message
                                self.renderer.state.lines.append(f"[TUI app detected: {cmd.split()[0]}]")
                                self.renderer.state.lines.append("")
                                self.renderer.state.lines.append("TUI apps require --terminal mode on Windows:")
                                self.renderer.state.lines.append(f"  termgif script.tg --terminal")
                                self.renderer.state.lines.append("")
                                self.renderer.state.current_line = self.renderer.state.prompt
                                self.capture_frame(2000)
                            elif self.start_tui(cmd):
                                # Start TUI mode with PTY
                                in_tui_mode = True

                                # Wait for TUI to initialize
                                if self._wait_for_pty_content(timeout_ms=3000):
                                    self._capture_pty_frames(500)
                                else:
                                    time.sleep(0.5)
                                    self._render_pty_screen()
                                    self.capture_frame(100)
                            else:
                                # PTY failed
                                self.renderer.state.lines.append(f"[Failed to start TUI: {cmd}]")
                                self.renderer.state.lines.append("")
                                self.renderer.state.current_line = self.renderer.state.prompt
                                self.capture_frame(100)
                        else:
                            # Regular command
                            output = self.execute_command(cmd)
                            self._add_output_animated(output)

                    current_cmd = ""

            elif isinstance(action, SleepAction):
                if in_tui_mode:
                    self._capture_pty_frames(action.ms)
                else:
                    self.capture_frame(action.ms)

            elif isinstance(action, KeyAction):
                if in_tui_mode:
                    self.send_tui_key(action.key)
                    time.sleep(0.1)
                    self._render_pty_screen()
                    self.capture_frame(100)
                    self._capture_pty_frames(100)
                else:
                    self.capture_frame(100)

        # Cleanup TUI if still running
        if in_tui_mode:
            self.stop_tui()

        self.capture_frame(self.config.end_delay)


def record_live(script_path: Path, output: Path | None = None, native_colors: bool = False) -> Path:
    """Record script with real command execution.

    Args:
        script_path: Path to the script file
        output: Optional output path override
        native_colors: If True, preserve TUI app's native colors

    Returns:
        Path to the created output file
    """
    from ..parser import parse_script

    config, actions = parse_script(script_path)

    # CLI flag overrides config
    if native_colors:
        config.native_colors = True

    # Determine output path
    if output:
        output_path = output
    elif config.output:
        output_path = Path(config.output)
    else:
        output_path = script_path.with_suffix(".gif")

    # Ensure extension
    if not output_path.suffix:
        output_path = output_path.with_suffix(".gif")

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    recorder = LiveRecorder(config)
    recorder.run_actions(actions)
    recorder.save_gif(output_path)

    return output_path
