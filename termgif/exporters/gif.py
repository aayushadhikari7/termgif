"""GIF exporter using PIL and optionally ffmpeg for better quality."""
from pathlib import Path
from PIL import Image
import tempfile
import shutil
import os

from .base import BaseExporter, register_exporter
from ..config import TapeConfig


@register_exporter
class GifExporter(BaseExporter):
    """Export frames as animated GIF.

    Uses PIL for simple GIF creation, or ffmpeg for better quality
    with palette optimization.
    """

    format_name = "GIF"
    extensions = ["gif"]
    requires_ffmpeg = False  # PIL can do it, ffmpeg is optional

    def export(self, output_path: Path) -> Path:
        """Export frames as GIF."""
        self.validate()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Try ffmpeg first for better quality
        try:
            return self._export_ffmpeg(output_path)
        except (RuntimeError, FileNotFoundError):
            # Fall back to PIL
            return self._export_pil(output_path)

    def _export_pil(self, output_path: Path) -> Path:
        """Export using PIL (built-in, lower quality)."""
        self.frames[0].save(
            output_path,
            save_all=True,
            append_images=self.frames[1:],
            duration=self.durations,
            loop=self.config.loop,
            optimize=self.config.optimize,
        )
        return output_path

    def _export_ffmpeg(self, output_path: Path) -> Path:
        """Export using ffmpeg (better quality with palette generation)."""
        from ..utils.ffmpeg import check_ffmpeg

        if not check_ffmpeg():
            raise RuntimeError("ffmpeg not available")

        import subprocess
        import numpy as np

        # Create temp directory for frames
        temp_dir = tempfile.mkdtemp(prefix="termgif_")

        try:
            # Calculate average fps from durations
            avg_duration = sum(self.durations) / len(self.durations)
            fps = max(1, int(1000 / avg_duration))

            # Save frames as PNGs
            for i, frame in enumerate(self.frames):
                if frame.mode != "RGB":
                    frame = frame.convert("RGB")
                frame_path = os.path.join(temp_dir, f"frame_{i:05d}.png")
                frame.save(frame_path, "PNG")

            # Build ffmpeg command with palette generation
            input_pattern = os.path.join(temp_dir, "frame_%05d.png")

            # Dithering options
            dither = self.config.dither.replace("-", "_")
            colors = min(256, self.config.colors)

            filter_graph = (
                f"split[s0][s1];"
                f"[s0]palettegen=max_colors={colors}[p];"
                f"[s1][p]paletteuse=dither={dither}"
            )

            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", input_pattern,
                "-vf", filter_graph,
                "-loop", str(self.config.loop),
                str(output_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg failed: {result.stderr}")

            return output_path

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
