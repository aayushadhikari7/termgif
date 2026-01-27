"""Base exporter class and factory functions."""
from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image

from ..config import TapeConfig


class BaseExporter(ABC):
    """Abstract base class for all exporters.

    Exporters handle converting a sequence of frames into various output formats
    (GIF, WebP, MP4, WebM, APNG, SVG, PNG frames, etc.).
    """

    # Class attributes that subclasses should override
    format_name: str = ""
    extensions: list[str] = []
    requires_ffmpeg: bool = False

    def __init__(self, frames: list[Image.Image], durations: list[int], config: TapeConfig):
        """Initialize the exporter.

        Args:
            frames: List of PIL Image frames
            durations: List of frame durations in milliseconds
            config: Recording configuration
        """
        self.frames = frames
        self.durations = durations
        self.config = config

    @abstractmethod
    def export(self, output_path: Path) -> Path:
        """Export frames to the output file.

        Args:
            output_path: Path to write the output file

        Returns:
            Path to the created file

        Raises:
            RuntimeError: If export fails
        """
        pass

    @classmethod
    def supports_format(cls, ext: str) -> bool:
        """Check if this exporter supports a file extension.

        Args:
            ext: File extension (with or without leading dot)

        Returns:
            True if this exporter supports the extension
        """
        ext = ext.lower().lstrip(".")
        return ext in cls.extensions

    def validate(self) -> None:
        """Validate that export can proceed.

        Raises:
            ValueError: If validation fails
            RuntimeError: If dependencies are missing
        """
        if not self.frames:
            raise ValueError("No frames to export")

        if len(self.frames) != len(self.durations):
            raise ValueError(
                f"Frame count ({len(self.frames)}) doesn't match "
                f"duration count ({len(self.durations)})"
            )

        if self.requires_ffmpeg:
            from ..utils.ffmpeg import check_ffmpeg
            if not check_ffmpeg():
                raise RuntimeError(
                    f"{self.format_name} export requires ffmpeg. "
                    "Please install ffmpeg and add it to PATH."
                )


# Registry of exporters
_EXPORTERS: dict[str, type[BaseExporter]] = {}


def register_exporter(exporter_class: type[BaseExporter]) -> type[BaseExporter]:
    """Register an exporter class.

    Args:
        exporter_class: The exporter class to register

    Returns:
        The exporter class (for use as decorator)
    """
    for ext in exporter_class.extensions:
        _EXPORTERS[ext] = exporter_class
    return exporter_class


def get_exporter(format_or_path: str) -> type[BaseExporter]:
    """Get the appropriate exporter for a format or file path.

    Args:
        format_or_path: Format name (e.g., "gif") or file path (e.g., "output.mp4")

    Returns:
        Exporter class

    Raises:
        ValueError: If no exporter found for the format
    """
    # Check if it's a path
    if "/" in format_or_path or "\\" in format_or_path or "." in format_or_path:
        ext = Path(format_or_path).suffix.lower().lstrip(".")
    else:
        ext = format_or_path.lower()

    if ext in _EXPORTERS:
        return _EXPORTERS[ext]

    available = ", ".join(sorted(_EXPORTERS.keys()))
    raise ValueError(f"No exporter for format '{ext}'. Available: {available}")


def list_formats() -> list[str]:
    """Get list of supported export formats.

    Returns:
        Sorted list of format extensions
    """
    return sorted(set(_EXPORTERS.keys()))


def detect_format(output_path: str | Path, config: TapeConfig) -> str:
    """Detect the output format from path and config.

    Priority:
    1. Config format setting
    2. File extension
    3. Default to "gif"

    Args:
        output_path: Output file path
        config: Recording configuration

    Returns:
        Format string (e.g., "gif", "mp4")
    """
    # Check config first
    if config.format and config.format != "gif":
        return config.format.lower()

    # Check file extension
    path = Path(output_path)
    if path.suffix:
        ext = path.suffix.lower().lstrip(".")
        if ext in _EXPORTERS:
            return ext

    # Default to gif
    return "gif"
