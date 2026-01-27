"""Base recorder class for all recording modes."""
from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image

from ..config import TapeConfig
from ..actions import Action, TypeAction, EnterAction, SleepAction, KeyAction
from ..renderer import TerminalRenderer, TerminalStyle


class BaseRecorder(ABC):
    """Abstract base class for all recorders.

    Provides common functionality for capturing frames and saving output.
    Subclasses implement specific recording modes (simulated, live, terminal capture).
    """

    def __init__(self, config: TapeConfig):
        """Initialize the recorder.

        Args:
            config: Recording configuration
        """
        self.config = config
        self.frames: list[Image.Image] = []
        self.frame_durations: list[int] = []

        # Set up renderer
        self._setup_renderer()

    def _setup_renderer(self) -> None:
        """Set up the terminal renderer based on config."""
        # Use specific radius if set, otherwise fall back to general radius
        inner_r = self.config.radius_inner if self.config.radius_inner is not None else self.config.radius
        outer_r = self.config.radius_outer if self.config.radius_outer is not None else self.config.radius

        style = TerminalStyle(
            width=self.config.width,
            height=self.config.height,
            font_size=self.config.font_size,
            title=self.config.title,
            scale=self.config.quality,
            chrome=self.config.chrome,
            theme=self.config.theme,
            padding=self.config.padding,
            prompt=self.config.prompt,
            cursor=self.config.cursor,
            corner_radius=inner_r,
            outer_radius=outer_r,
        )
        self.renderer = TerminalRenderer(style)

    def capture_frame(self, duration_ms: int = 100) -> None:
        """Capture the current terminal state as a frame.

        Args:
            duration_ms: Duration to display this frame in milliseconds
        """
        frame = self.renderer.render()
        self.frames.append(frame)
        self.frame_durations.append(duration_ms)

    @abstractmethod
    def run_actions(self, actions: list[Action]) -> None:
        """Execute all actions and capture frames.

        Args:
            actions: List of actions to execute
        """
        pass

    def save(self, output_path: Path, format: str | None = None) -> Path:
        """Save captured frames to output file.

        Args:
            output_path: Path to save the output
            format: Output format (auto-detected from path if not specified)

        Returns:
            Path to the saved file

        Raises:
            ValueError: If no frames captured
        """
        if not self.frames:
            raise ValueError("No frames captured")

        from ..exporters import get_exporter, detect_format

        # Determine format
        if format is None:
            format = detect_format(output_path, self.config)

        # Get appropriate exporter
        exporter_class = get_exporter(format)
        exporter = exporter_class(self.frames, self.frame_durations, self.config)

        # Export
        return exporter.export(Path(output_path))

    def save_gif(self, output_path: Path) -> Path:
        """Save captured frames as GIF (legacy method).

        Args:
            output_path: Path to save the GIF

        Returns:
            Path to the saved file
        """
        return self.save(output_path, format="gif")
