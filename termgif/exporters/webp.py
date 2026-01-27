"""WebP exporter for animated WebP output."""
from pathlib import Path
from PIL import Image

from .base import BaseExporter, register_exporter
from ..config import TapeConfig


@register_exporter
class WebPExporter(BaseExporter):
    """Export frames as animated WebP.

    WebP offers better compression than GIF while supporting
    full color and transparency.
    """

    format_name = "WebP"
    extensions = ["webp"]
    requires_ffmpeg = False

    def export(self, output_path: Path) -> Path:
        """Export frames as animated WebP."""
        self.validate()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert frames to RGBA if needed
        frames = []
        for frame in self.frames:
            if frame.mode not in ("RGB", "RGBA"):
                frame = frame.convert("RGBA")
            frames.append(frame)

        # Calculate quality
        quality = self.config.lossy
        lossless = quality >= 100

        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=self.durations,
            loop=self.config.loop,
            quality=quality,
            lossless=lossless,
        )

        return output_path
