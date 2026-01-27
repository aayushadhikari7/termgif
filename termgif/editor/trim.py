"""Trim recordings by cutting start/end."""
from pathlib import Path
from PIL import Image

from ..config import TapeConfig


def trim_recording(
    input_path: Path,
    output_path: Path | None = None,
    start_ms: int = 0,
    end_ms: int | None = None,
) -> Path:
    """Trim a recording by cutting frames from start and/or end.

    Args:
        input_path: Path to the input file (GIF, WebP)
        output_path: Path for output (defaults to input_trimmed.ext)
        start_ms: Milliseconds to cut from the start
        end_ms: Milliseconds to cut from the end (negative = from end)

    Returns:
        Path to the trimmed file
    """
    input_path = Path(input_path)

    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_trimmed{input_path.suffix}"
    else:
        output_path = Path(output_path)

    # Open the image
    img = Image.open(input_path)

    # Get all frames and durations
    frames = []
    durations = []

    try:
        while True:
            frames.append(img.copy())
            durations.append(img.info.get('duration', 100))
            img.seek(img.tell() + 1)
    except EOFError:
        pass

    if not frames:
        raise ValueError("No frames found in input file")

    # Calculate cumulative time
    cumulative = [0]
    for d in durations:
        cumulative.append(cumulative[-1] + d)

    total_duration = cumulative[-1]

    # Handle negative end_ms (from end)
    if end_ms is not None and end_ms < 0:
        end_ms = total_duration + end_ms

    if end_ms is None:
        end_ms = total_duration

    # Validate
    if start_ms >= end_ms:
        raise ValueError("Start time must be less than end time")
    if start_ms < 0:
        start_ms = 0
    if end_ms > total_duration:
        end_ms = total_duration

    # Find frame indices
    start_idx = 0
    end_idx = len(frames)

    for i, t in enumerate(cumulative[:-1]):
        if t < start_ms:
            start_idx = i + 1
        if cumulative[i + 1] > end_ms and end_idx == len(frames):
            end_idx = i + 1

    # Extract frames
    trimmed_frames = frames[start_idx:end_idx]
    trimmed_durations = durations[start_idx:end_idx]

    if not trimmed_frames:
        raise ValueError("No frames remain after trimming")

    # Adjust first and last frame durations
    if start_idx > 0:
        trimmed_durations[0] = cumulative[start_idx + 1] - start_ms
    if end_idx < len(frames):
        trimmed_durations[-1] = end_ms - cumulative[end_idx - 1]

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)

    trimmed_frames[0].save(
        output_path,
        save_all=True,
        append_images=trimmed_frames[1:],
        duration=trimmed_durations,
        loop=0,
        optimize=True,
    )

    return output_path
