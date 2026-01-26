"""Recorder - runs script and captures frames to GIF."""
from pathlib import Path
from PIL import Image

from .tape import TapeConfig, TypeAction, EnterAction, SleepAction, KeyAction, parse_tape
from .tg_parser import parse_tg
from .renderer import TerminalRenderer, TerminalStyle


class Recorder:
    """Records terminal session to GIF."""

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
        self.frame_durations: list[int] = []  # ms per frame

    def capture_frame(self, duration_ms: int = 100) -> None:
        """Capture current terminal state as a frame."""
        frame = self.renderer.render()
        self.frames.append(frame)
        self.frame_durations.append(duration_ms)

    def run_action(self, action, typing_speed_ms: int = 50) -> None:
        """Execute a single action."""
        if isinstance(action, TypeAction):
            # Type each character with frame capture
            for char in action.text:
                self.renderer.type_char(char)
                self.capture_frame(typing_speed_ms)

        elif isinstance(action, EnterAction):
            # Press enter and execute command
            cmd = self.renderer.press_enter()
            self.capture_frame(100)

            if cmd and not cmd.startswith("#"):
                output = self.renderer.execute_command(cmd)
                self.renderer.add_output(output)
                self.capture_frame(100)

        elif isinstance(action, SleepAction):
            # Just hold the current frame
            self.capture_frame(action.ms)

        elif isinstance(action, KeyAction):
            # KeyAction is only meaningful in --terminal mode
            # In simulated mode, we just pause briefly
            print(f"[Note: 'key \"{action.key}\"' requires --terminal mode for TUI interaction]")
            self.capture_frame(100)

    def run_tape(self, actions: list) -> None:
        """Run all actions from tape."""
        # Initial frame
        self.capture_frame(self.config.start_delay)

        for action in actions:
            self.run_action(action, self.config.typing_speed_ms)

        # Final frame - hold a bit longer
        self.capture_frame(self.config.end_delay)

    def save_gif(self, output_path: str | Path) -> None:
        """Save frames as animated GIF."""
        output_path = Path(output_path)

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

        print(f"Saved GIF to {output_path} ({len(self.frames)} frames)")


def parse_script(path: Path) -> tuple[TapeConfig, list]:
    """Parse a script file (.tg or .tape)."""
    suffix = path.suffix.lower()
    if suffix == ".tg":
        return parse_tg(path)
    elif suffix == ".tape":
        return parse_tape(path)
    else:
        raise ValueError(f"Unknown file type: {suffix}. Use .tg or .tape")


def record_script(script_path: Path, output_path: Path | None = None, bare: bool = False) -> Path:
    """Record a script file to GIF."""
    config, actions = parse_script(script_path)

    if output_path:
        config.output = str(output_path)

    if bare:
        config.chrome = False

    recorder = Recorder(config)
    recorder.run_tape(actions)

    out = Path(config.output)
    recorder.save_gif(out)

    return out
