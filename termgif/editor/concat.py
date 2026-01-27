"""Concatenate multiple recordings."""
from pathlib import Path
from PIL import Image


def concatenate(
    input_paths: list[Path],
    output_path: Path,
    transition_ms: int = 0,
) -> Path:
    """Concatenate multiple recordings into one.

    Args:
        input_paths: List of input file paths
        output_path: Path for output
        transition_ms: Optional pause between recordings in ms

    Returns:
        Path to the concatenated file
    """
    if not input_paths:
        raise ValueError("No input files provided")

    all_frames = []
    all_durations = []

    for path in input_paths:
        path = Path(path)
        img = Image.open(path)

        frames = []
        durations = []

        try:
            while True:
                frames.append(img.copy())
                durations.append(img.info.get('duration', 100))
                img.seek(img.tell() + 1)
        except EOFError:
            pass

        if frames:
            all_frames.extend(frames)
            all_durations.extend(durations)

            # Add transition pause
            if transition_ms > 0 and path != input_paths[-1]:
                # Hold last frame for transition duration
                all_durations[-1] += transition_ms

    if not all_frames:
        raise ValueError("No frames found in input files")

    # Ensure consistent size (use first frame as reference)
    ref_size = all_frames[0].size
    resized_frames = []
    for frame in all_frames:
        if frame.size != ref_size:
            frame = frame.resize(ref_size, Image.Resampling.LANCZOS)
        resized_frames.append(frame)

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    resized_frames[0].save(
        output_path,
        save_all=True,
        append_images=resized_frames[1:],
        duration=all_durations,
        loop=0,
        optimize=True,
    )

    return output_path
