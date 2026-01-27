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
            # We just show the typing, no output (safe and honest)
            self.renderer.press_enter()
            self.capture_frame(100)
            # Restore the prompt for the next line
            self.renderer.state.current_line = self.renderer.state.prompt

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
