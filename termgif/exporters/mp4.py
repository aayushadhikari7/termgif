"""MP4 video exporter using ffmpeg."""
from pathlib import Path
import tempfile
import shutil
import os
import subprocess

from .base import BaseExporter, register_exporter
from ..config import TapeConfig


@register_exporter
class MP4Exporter(BaseExporter):
    """Export frames as MP4 video.

    Uses ffmpeg for encoding. Produces very small files suitable
    for long recordings.
    """

    format_name = "MP4"
    extensions = ["mp4"]
    requires_ffmpeg = True

    def export(self, output_path: Path) -> Path:
        """Export frames as MP4 video."""
        self.validate()

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create temp directory for frames
        temp_dir = tempfile.mkdtemp(prefix="termgif_mp4_")

        try:
            # Calculate fps from durations
            avg_duration = sum(self.durations) / len(self.durations)
            fps = max(1, int(1000 / avg_duration))

            # Save frames as PNGs
            for i, frame in enumerate(self.frames):
                if frame.mode != "RGB":
                    frame = frame.convert("RGB")
                frame_path = os.path.join(temp_dir, f"frame_{i:05d}.png")
                frame.save(frame_path, "PNG")

            input_pattern = os.path.join(temp_dir, "frame_%05d.png")

            # Select codec
            codec = self.config.codec
            if codec == "h264":
                codec = "libx264"
            elif codec == "h265":
                codec = "libx265"

            # Build ffmpeg command
            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", input_pattern,
                "-c:v", codec,
                "-pix_fmt", "yuv420p",  # Compatibility
                "-preset", "medium",
            ]

            # Add bitrate or CRF
            if self.config.bitrate and self.config.bitrate != "2M":
                cmd.extend(["-b:v", self.config.bitrate])
            else:
                cmd.extend(["-crf", str(self.config.crf)])

            cmd.append(str(output_path))

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
