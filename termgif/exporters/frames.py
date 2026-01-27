"""PNG frames exporter for manual editing."""
from pathlib import Path
import json

from .base import BaseExporter, register_exporter
from ..config import TapeConfig


@register_exporter
class FramesExporter(BaseExporter):
    """Export frames as individual PNG files.

    Useful for manual editing in video editors or image tools.
    Also exports a metadata JSON file with timing info.
    """

    format_name = "PNG Frames"
    extensions = ["frames"]
    requires_ffmpeg = False

    def export(self, output_path: Path) -> Path:
        """Export frames as individual PNG files."""
        self.validate()

        output_path = Path(output_path)

        # If path has extension, use parent directory + stem as folder name
        if output_path.suffix:
            output_dir = output_path.parent / output_path.stem
        else:
            output_dir = output_path

        output_dir.mkdir(parents=True, exist_ok=True)

        # Export each frame
        frame_files = []
        for i, (frame, duration) in enumerate(zip(self.frames, self.durations)):
            frame_path = output_dir / f"frame_{i:05d}.png"
            if frame.mode != "RGB":
                frame = frame.convert("RGB")
            frame.save(frame_path, "PNG", optimize=self.config.optimize)
            frame_files.append({
                "filename": frame_path.name,
                "duration_ms": duration,
                "index": i
            })

        # Export metadata
        metadata = {
            "format": "termgif_frames",
            "version": "1.0",
            "frame_count": len(self.frames),
            "total_duration_ms": sum(self.durations),
            "loop": self.config.loop,
            "width": self.frames[0].size[0] if self.frames else 0,
            "height": self.frames[0].size[1] if self.frames else 0,
            "frames": frame_files
        }

        metadata_path = output_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return output_dir
