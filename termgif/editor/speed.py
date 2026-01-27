"""Change playback speed of recordings."""
from pathlib import Path
from PIL import Image


def change_speed(
    input_path: Path,
    output_path: Path | None = None,
    speed: float = 1.0,
) -> Path:
    """Change the playback speed of a recording.

    Args:
        input_path: Path to the input file (GIF, WebP)
        output_path: Path for output (defaults to input_Nx.ext)
        speed: Speed multiplier (2.0 = 2x faster, 0.5 = half speed)

    Returns:
        Path to the modified file
    """
    if speed <= 0:
        raise ValueError("Speed must be positive")

    input_path = Path(input_path)

    if output_path is None:
        speed_str = f"{speed}x".replace(".", "_")
        output_path = input_path.parent / f"{input_path.stem}_{speed_str}{input_path.suffix}"
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

    # Adjust durations
    new_durations = [max(10, int(d / speed)) for d in durations]

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=new_durations,
        loop=0,
        optimize=True,
    )

    return output_path
