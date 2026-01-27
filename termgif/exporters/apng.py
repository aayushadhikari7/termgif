"""APNG (Animated PNG) exporter."""
from pathlib import Path
from PIL import Image

from .base import BaseExporter, register_exporter
from ..config import TapeConfig


@register_exporter
class APNGExporter(BaseExporter):
    """Export frames as Animated PNG.

    APNG supports full color and transparency while being
    backwards compatible with static PNG viewers.
    """

    format_name = "APNG"
    extensions = ["apng", "png"]
    requires_ffmpeg = False

    def export(self, output_path: Path) -> Path:
        """Export frames as APNG."""
        self.validate()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure .apng extension if not .png
        if output_path.suffix.lower() not in (".apng", ".png"):
            output_path = output_path.with_suffix(".apng")

        # Convert frames to RGBA if needed for transparency support
        frames = []
        for frame in self.frames:
            if frame.mode not in ("RGB", "RGBA"):
                frame = frame.convert("RGBA")
            frames.append(frame)

        # PIL supports APNG natively in newer versions
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=self.durations,
            loop=self.config.loop,
            optimize=self.config.optimize,
        )

        return output_path
