"""Add overlays (watermarks, captions) to recordings."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def add_watermark(
    input_path: Path,
    watermark_path: Path,
    output_path: Path | None = None,
    position: str = "bottom-right",
    opacity: float = 0.5,
    margin: int = 10,
) -> Path:
    """Add a watermark image to all frames.

    Args:
        input_path: Path to the input file
        watermark_path: Path to the watermark image
        output_path: Path for output (defaults to input_watermarked.ext)
        position: Position (top-left, top-right, bottom-left, bottom-right, center)
        opacity: Watermark opacity (0.0 - 1.0)
        margin: Margin from edges in pixels

    Returns:
        Path to the watermarked file
    """
    input_path = Path(input_path)
    watermark_path = Path(watermark_path)

    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_watermarked{input_path.suffix}"
    else:
        output_path = Path(output_path)

    # Load watermark
    watermark = Image.open(watermark_path).convert("RGBA")

    # Adjust watermark opacity
    if opacity < 1.0:
        alpha = watermark.split()[3]
        alpha = alpha.point(lambda p: int(p * opacity))
        watermark.putalpha(alpha)

    # Open the input
    img = Image.open(input_path)

    frames = []
    durations = []

    try:
        while True:
            frame = img.copy().convert("RGBA")

            # Calculate position
            w, h = frame.size
            wm_w, wm_h = watermark.size

            if position == "top-left":
                pos = (margin, margin)
            elif position == "top-right":
                pos = (w - wm_w - margin, margin)
            elif position == "bottom-left":
                pos = (margin, h - wm_h - margin)
            elif position == "bottom-right":
                pos = (w - wm_w - margin, h - wm_h - margin)
            elif position == "center":
                pos = ((w - wm_w) // 2, (h - wm_h) // 2)
            else:
                pos = (w - wm_w - margin, h - wm_h - margin)

            # Composite
            frame.paste(watermark, pos, watermark)
            frames.append(frame.convert("RGB"))
            durations.append(img.info.get('duration', 100))

            img.seek(img.tell() + 1)
    except EOFError:
        pass

    if not frames:
        raise ValueError("No frames found in input file")

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )

    return output_path


def add_caption(
    input_path: Path,
    caption: str,
    output_path: Path | None = None,
    position: str = "bottom",
    font_size: int = 24,
    color: str = "#ffffff",
    bg_color: str = "#000000",
    bg_opacity: float = 0.7,
    padding: int = 10,
) -> Path:
    """Add a text caption to all frames.

    Args:
        input_path: Path to the input file
        caption: Caption text
        output_path: Path for output (defaults to input_captioned.ext)
        position: Position (top or bottom)
        font_size: Font size in pixels
        color: Text color (hex)
        bg_color: Background color (hex)
        bg_opacity: Background opacity
        padding: Padding around text

    Returns:
        Path to the captioned file
    """
    input_path = Path(input_path)

    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_captioned{input_path.suffix}"
    else:
        output_path = Path(output_path)

    # Try to get a font
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    # Open the input
    img = Image.open(input_path)

    frames = []
    durations = []

    try:
        while True:
            frame = img.copy().convert("RGBA")
            w, h = frame.size

            # Create overlay
            overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            # Calculate text size
            bbox = draw.textbbox((0, 0), caption, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            # Calculate positions
            bar_h = text_h + padding * 2
            if position == "top":
                bar_y = 0
                text_y = padding
            else:
                bar_y = h - bar_h
                text_y = h - bar_h + padding

            text_x = (w - text_w) // 2

            # Draw background bar
            bg_r = int(bg_color[1:3], 16)
            bg_g = int(bg_color[3:5], 16)
            bg_b = int(bg_color[5:7], 16)
            bg_a = int(255 * bg_opacity)
            draw.rectangle([(0, bar_y), (w, bar_y + bar_h)], fill=(bg_r, bg_g, bg_b, bg_a))

            # Draw text
            draw.text((text_x, text_y), caption, font=font, fill=color)

            # Composite
            frame = Image.alpha_composite(frame, overlay)
            frames.append(frame.convert("RGB"))
            durations.append(img.info.get('duration', 100))

            img.seek(img.tell() + 1)
    except EOFError:
        pass

    if not frames:
        raise ValueError("No frames found in input file")

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )

    return output_path
