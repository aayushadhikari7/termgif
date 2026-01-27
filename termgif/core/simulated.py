"""Simulated recorder - renders without executing commands."""
from pathlib import Path

from .recorder import BaseRecorder
from ..config import TapeConfig
from ..actions import Action, TypeAction, EnterAction, SleepAction, KeyAction


class SimulatedRecorder(BaseRecorder):
    """Records terminal session in simulated mode.

    Commands are displayed but NOT actually executed.
    This is safe mode - no real commands run.
    """

    def _generate_fake_output(self, cmd: str) -> str:
        """Generate fake output for common commands in simulate mode.

        This ensures --simulate NEVER runs real commands.
        """
        cmd_lower = cmd.lower().strip()

        # Common commands with fake outputs
        if cmd_lower.startswith("echo "):
            # Echo just returns what's after echo
            return cmd[5:].strip().strip("'\"")

        if cmd_lower == "ls" or cmd_lower.startswith("ls "):
            return "file1.txt  file2.txt  folder/"

        if cmd_lower == "pwd":
            return "/home/user/project"

        if cmd_lower.startswith("cat "):
            return "[file contents]"

        if cmd_lower == "git status":
            return "On branch main\nnothing to commit, working tree clean"

        if cmd_lower == "git log" or cmd_lower.startswith("git log "):
            return "commit abc123\nAuthor: User\nDate: Today\n\n    Initial commit"

        if cmd_lower.startswith("git "):
            return ""  # Other git commands: no output (safe)

        if cmd_lower == "npm list" or cmd_lower.startswith("npm list "):
            return "project@1.0.0\n+-- package@1.0.0"

        if cmd_lower.startswith("python") or cmd_lower.startswith("python3"):
            return ""

        if cmd_lower == "docker ps":
            return "CONTAINER ID   IMAGE   STATUS"

        if cmd_lower == "docker images":
            return "REPOSITORY   TAG   IMAGE ID"

        if cmd_lower.startswith("curl "):
            return '{"status": "ok"}'

        if cmd_lower == "whoami":
            return "user"

        if cmd_lower == "date":
            return "Mon Jan 27 12:00:00 UTC 2025"

        # Default: return empty (no output shown)
        return ""

    def run_action(self, action: Action) -> None:
        """Execute a single action.

        Args:
            action: The action to execute
        """
        if isinstance(action, TypeAction):
            # Type each character with frame capture
            for char in action.text:
                self.renderer.type_char(char)
                self.capture_frame(self.config.typing_speed_ms)

        elif isinstance(action, EnterAction):
            # Press enter - but DO NOT execute command in simulate mode!
            cmd = self.renderer.press_enter()
            self.capture_frame(100)

            # In simulate mode, show fake output instead of running real commands
            if cmd and not cmd.startswith("#"):
                fake_output = self._generate_fake_output(cmd)
                if fake_output:
                    self.renderer.add_output(fake_output)
                    self.capture_frame(100)

        elif isinstance(action, SleepAction):
            # Just hold the current frame
            self.capture_frame(action.duration_ms)

        elif isinstance(action, KeyAction):
            # KeyAction is only meaningful in --terminal mode
            # In simulated mode, we just pause briefly
            print(f"[Note: 'key \"{action.key}\"' requires --terminal mode for TUI interaction]")
            self.capture_frame(100)

    def run_actions(self, actions: list[Action]) -> None:
        """Run all actions from tape.

        Args:
            actions: List of actions to execute
        """
        # Initial frame
        self.capture_frame(self.config.start_delay)

        for action in actions:
            self.run_action(action)

        # Final frame - hold a bit longer
        self.capture_frame(self.config.end_delay)


def record_script(script_path: Path, output_path: Path | None = None, bare: bool = False) -> Path:
    """Record a script file in simulated mode (NO real commands executed).

    Args:
        script_path: Path to the script file (.tg or .tape)
        output_path: Optional output path override
        bare: If True, render without window chrome

    Returns:
        Path to the created output file
    """
    from ..parser import parse_script

    config, actions = parse_script(script_path)

    if output_path:
        config.output = str(output_path)

    if bare:
        config.chrome = False

    recorder = SimulatedRecorder(config)
    recorder.run_actions(actions)

    out = Path(config.output)

    # Detect format from extension or config
    ext = out.suffix.lower().lstrip('.')
    if config.format and config.format != 'gif':
        fmt = config.format
    elif ext in ('webp', 'mp4', 'webm', 'png', 'apng', 'svg', 'cast'):
        fmt = ext
    else:
        fmt = 'gif'

    recorder.save(out, format=fmt)

    return out
