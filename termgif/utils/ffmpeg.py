"""FFmpeg wrapper utilities for video encoding."""
import subprocess
import shutil
from pathlib import Path


def check_ffmpeg() -> bool:
    """Check if ffmpeg is available.

    Returns:
        True if ffmpeg is available, False otherwise.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True
        )
        return result.returncode == 0
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_ffmpeg_path() -> str | None:
    """Get the path to ffmpeg executable.

    Returns:
        Path to ffmpeg or None if not found.
    """
    return shutil.which("ffmpeg")


def run_ffmpeg(args: list[str], capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run ffmpeg with the given arguments.

    Args:
        args: List of arguments to pass to ffmpeg (without 'ffmpeg' itself)
        capture_output: Whether to capture stdout/stderr

    Returns:
        CompletedProcess instance

    Raises:
        RuntimeError: If ffmpeg is not found
    """
    if not check_ffmpeg():
        raise RuntimeError("ffmpeg not found. Please install ffmpeg and add it to PATH.")

    cmd = ["ffmpeg"] + args

    return subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
        encoding='utf-8',
        errors='replace'
    )


def create_gif_from_frames(
    input_pattern: str,
    output_path: Path,
    fps: int = 10,
    loop: int = 0,
    optimize: bool = True,
    colors: int = 256,
    dither: str = "floyd_steinberg"
) -> Path:
    """Create a GIF from a sequence of frames using ffmpeg.

    Args:
        input_pattern: Input file pattern (e.g., "frame_%05d.png")
        output_path: Output GIF path
        fps: Frames per second
        loop: Loop count (0 = infinite)
        optimize: Whether to optimize the palette
        colors: Max colors in palette
        dither: Dithering algorithm

    Returns:
        Path to the created GIF

    Raises:
        RuntimeError: If ffmpeg fails
    """
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build filter graph for palette generation
    if optimize:
        filter_graph = f"split[s0][s1];[s0]palettegen=max_colors={colors}[p];[s1][p]paletteuse=dither={dither}"
    else:
        filter_graph = f"palettegen=max_colors={colors}"

    args = [
        "-y",
        "-framerate", str(fps),
        "-i", str(input_pattern),
        "-vf", filter_graph,
        "-loop", str(loop),
        str(output_path)
    ]

    result = run_ffmpeg(args)

    if result.returncode != 0:
        error_msg = result.stderr or result.stdout or "Unknown error"
        raise RuntimeError(f"ffmpeg failed: {error_msg}")

    return output_path


def create_video_from_frames(
    input_pattern: str,
    output_path: Path,
    fps: int = 30,
    codec: str = "libx264",
    crf: int = 23,
    bitrate: str | None = None,
    preset: str = "medium"
) -> Path:
    """Create a video from a sequence of frames using ffmpeg.

    Args:
        input_pattern: Input file pattern (e.g., "frame_%05d.png")
        output_path: Output video path
        fps: Frames per second
        codec: Video codec (libx264, libx265, libvpx-vp9, etc.)
        crf: Constant rate factor (quality, lower = better)
        bitrate: Target bitrate (e.g., "2M") - overrides crf if set
        preset: Encoding preset (ultrafast, fast, medium, slow, veryslow)

    Returns:
        Path to the created video

    Raises:
        RuntimeError: If ffmpeg fails
    """
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    args = [
        "-y",
        "-framerate", str(fps),
        "-i", str(input_pattern),
        "-c:v", codec,
        "-preset", preset,
        "-pix_fmt", "yuv420p",  # Compatibility
    ]

    if bitrate:
        args.extend(["-b:v", bitrate])
    else:
        args.extend(["-crf", str(crf)])

    args.append(str(output_path))

    result = run_ffmpeg(args)

    if result.returncode != 0:
        error_msg = result.stderr or result.stdout or "Unknown error"
        raise RuntimeError(f"ffmpeg failed: {error_msg}")

    return output_path


def create_webp_from_frames(
    input_pattern: str,
    output_path: Path,
    fps: int = 10,
    loop: int = 0,
    quality: int = 80,
    lossless: bool = False
) -> Path:
    """Create an animated WebP from a sequence of frames using ffmpeg.

    Args:
        input_pattern: Input file pattern (e.g., "frame_%05d.png")
        output_path: Output WebP path
        fps: Frames per second
        loop: Loop count (0 = infinite)
        quality: Quality (0-100, higher = better)
        lossless: Whether to use lossless compression

    Returns:
        Path to the created WebP

    Raises:
        RuntimeError: If ffmpeg fails
    """
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    args = [
        "-y",
        "-framerate", str(fps),
        "-i", str(input_pattern),
        "-c:v", "libwebp",
        "-loop", str(loop),
        "-quality", str(quality),
    ]

    if lossless:
        args.extend(["-lossless", "1"])

    args.append(str(output_path))

    result = run_ffmpeg(args)

    if result.returncode != 0:
        error_msg = result.stderr or result.stdout or "Unknown error"
        raise RuntimeError(f"ffmpeg failed: {error_msg}")

    return output_path
