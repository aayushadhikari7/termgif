"""Terminal renderer - high quality terminal screenshots."""
from dataclasses import dataclass, field
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import subprocess
import os

# Color themes
THEMES = {
    "mocha": {  # Catppuccin Mocha (default)
        "base": "#1e1e2e", "mantle": "#181825", "crust": "#11111b",
        "surface0": "#313244", "surface1": "#45475a", "surface2": "#585b70",
        "text": "#cdd6f4", "subtext1": "#bac2de", "subtext0": "#a6adc8",
        "red": "#f38ba8", "yellow": "#f9e2af", "green": "#a6e3a1",
        "blue": "#89b4fa", "lavender": "#b4befe", "mauve": "#cba6f7", "teal": "#94e2d5",
    },
    "latte": {  # Catppuccin Latte (light theme)
        "base": "#eff1f5", "mantle": "#e6e9ef", "crust": "#dce0e8",
        "surface0": "#ccd0da", "surface1": "#bcc0cc", "surface2": "#acb0be",
        "text": "#4c4f69", "subtext1": "#5c5f77", "subtext0": "#6c6f85",
        "red": "#d20f39", "yellow": "#df8e1d", "green": "#40a02b",
        "blue": "#1e66f5", "lavender": "#7287fd", "mauve": "#8839ef", "teal": "#179299",
    },
    "frappe": {  # Catppuccin Frappé
        "base": "#303446", "mantle": "#292c3c", "crust": "#232634",
        "surface0": "#414559", "surface1": "#51576d", "surface2": "#626880",
        "text": "#c6d0f5", "subtext1": "#b5bfe2", "subtext0": "#a5adce",
        "red": "#e78284", "yellow": "#e5c890", "green": "#a6d189",
        "blue": "#8caaee", "lavender": "#babbf1", "mauve": "#ca9ee6", "teal": "#81c8be",
    },
    "macchiato": {  # Catppuccin Macchiato
        "base": "#24273a", "mantle": "#1e2030", "crust": "#181926",
        "surface0": "#363a4f", "surface1": "#494d64", "surface2": "#5b6078",
        "text": "#cad3f5", "subtext1": "#b8c0e0", "subtext0": "#a5adcb",
        "red": "#ed8796", "yellow": "#eed49f", "green": "#a6da95",
        "blue": "#8aadf4", "lavender": "#b7bdf8", "mauve": "#c6a0f6", "teal": "#8bd5ca",
    },
    "dracula": {  # Dracula
        "base": "#282a36", "mantle": "#21222c", "crust": "#191a21",
        "surface0": "#44475a", "surface1": "#4d4f5c", "surface2": "#565761",
        "text": "#f8f8f2", "subtext1": "#e0e0e0", "subtext0": "#bfbfbf",
        "red": "#ff5555", "yellow": "#f1fa8c", "green": "#50fa7b",
        "blue": "#8be9fd", "lavender": "#bd93f9", "mauve": "#ff79c6", "teal": "#8be9fd",
    },
    "nord": {  # Nord
        "base": "#2e3440", "mantle": "#272c36", "crust": "#20242d",
        "surface0": "#3b4252", "surface1": "#434c5e", "surface2": "#4c566a",
        "text": "#eceff4", "subtext1": "#e5e9f0", "subtext0": "#d8dee9",
        "red": "#bf616a", "yellow": "#ebcb8b", "green": "#a3be8c",
        "blue": "#81a1c1", "lavender": "#b48ead", "mauve": "#b48ead", "teal": "#8fbcbb",
    },
    "tokyo": {  # Tokyo Night
        "base": "#1a1b26", "mantle": "#16161e", "crust": "#13131a",
        "surface0": "#24283b", "surface1": "#2f3549", "surface2": "#3b4261",
        "text": "#c0caf5", "subtext1": "#a9b1d6", "subtext0": "#9aa5ce",
        "red": "#f7768e", "yellow": "#e0af68", "green": "#9ece6a",
        "blue": "#7aa2f7", "lavender": "#bb9af7", "mauve": "#bb9af7", "teal": "#73daca",
    },
    "gruvbox": {  # Gruvbox Dark
        "base": "#282828", "mantle": "#1d2021", "crust": "#171717",
        "surface0": "#3c3836", "surface1": "#504945", "surface2": "#665c54",
        "text": "#ebdbb2", "subtext1": "#d5c4a1", "subtext0": "#bdae93",
        "red": "#fb4934", "yellow": "#fabd2f", "green": "#b8bb26",
        "blue": "#83a598", "lavender": "#d3869b", "mauve": "#d3869b", "teal": "#8ec07c",
    },
}

# Default theme
COLORS = THEMES["mocha"]


@dataclass
class TerminalStyle:
    """Terminal appearance settings."""
    width: int = 80
    height: int = 24
    font_size: int = 14
    padding: int = 20
    line_height: float = 1.4
    title: str = "termgif"
    chrome: bool = True
    theme: str = "mocha"
    prompt: str = ""  # Custom prompt
    cursor: str = "block"  # block, bar, underline

    # Window chrome
    title_bar_height: int = 52
    button_radius: int = 7
    button_spacing: int = 9
    corner_radius: int = 12  # Inner window corner radius
    outer_radius: int = 10   # Outer GIF edge radius

    # Quality settings
    scale: int = 2
    shadow_blur: int = 25
    shadow_offset: int = 8


@dataclass
class StyledCell:
    """A cell with styling info for native color rendering."""
    char: str = " "
    fg: str = "text"
    bg: str = "base"
    bold: bool = False


@dataclass
class TerminalState:
    """Current state of the terminal."""
    lines: list[str] = field(default_factory=list)
    current_line: str = ""
    prompt: str = ""
    cwd: str = ""
    # Styled lines for native color mode (list of lists of StyledCell)
    styled_lines: list[list[StyledCell]] | None = None

    def __post_init__(self):
        self.cwd = os.getcwd()
        self._update_prompt()
        self.current_line = self.prompt

    def _update_prompt(self):
        user = os.environ.get("USER", os.environ.get("USERNAME", "user"))
        path = os.path.basename(self.cwd) or "~"
        self.prompt = f"{user}@{path} $ "


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def get_font(size: int) -> ImageFont.FreeTypeFont:
    """Get a high-quality monospace font."""
    font_paths = [
        # Windows
        "C:/Windows/Fonts/CascadiaCode.ttf",
        "C:/Windows/Fonts/CascadiaMono.ttf",
        "C:/Windows/Fonts/consola.ttf",
        # macOS
        "/System/Library/Fonts/SFMono.ttf",
        "/Library/Fonts/SF-Mono-Regular.otf",
        "/System/Library/Fonts/Monaco.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/TTF/JetBrainsMono-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
    ]

    # Try font paths first
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue

    # Try font names
    font_names = [
        "Cascadia Code", "Cascadia Mono", "JetBrains Mono",
        "Fira Code", "SF Mono", "Consolas", "Monaco", "Menlo",
        "DejaVu Sans Mono", "Ubuntu Mono", "Courier New",
    ]

    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue

    return ImageFont.load_default()


def create_rounded_rectangle_mask(size: tuple[int, int], radius: int) -> Image.Image:
    """Create an anti-aliased rounded rectangle mask."""
    # Create at higher resolution for smoother edges
    scale = 4
    w, h = size[0] * scale, size[1] * scale
    r = radius * scale

    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)

    # Draw rounded rectangle
    draw.rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)

    # Scale down with anti-aliasing
    return mask.resize(size, Image.LANCZOS)


class TerminalRenderer:
    """Renders terminal state to high-quality images."""

    def __init__(self, style: TerminalStyle | None = None):
        self.style = style or TerminalStyle()
        s = self.style

        # Get theme colors
        self.colors = THEMES.get(s.theme, THEMES["mocha"])

        # Scale up font for high-res rendering
        self.font = get_font(s.font_size * s.scale)
        self.title_font = get_font(int(s.font_size * s.scale * 0.9))
        self.state = TerminalState()

        # Apply custom prompt if specified
        if s.prompt:
            self.state.prompt = s.prompt
            self.state.current_line = s.prompt

        # Calculate character dimensions at scaled size
        bbox = self.font.getbbox("M")
        self.char_width = bbox[2] - bbox[0]
        self.char_height = int((bbox[3] - bbox[1]) * s.line_height)

    def type_char(self, char: str) -> None:
        self.state.current_line += char

    def type_text(self, text: str) -> None:
        for char in text:
            self.type_char(char)

    def press_enter(self) -> str:
        self.state.lines.append(self.state.current_line)
        cmd = self.state.current_line
        if self.state.prompt and cmd.startswith(self.state.prompt):
            cmd = cmd[len(self.state.prompt):]
        self.state.current_line = ""
        return cmd.strip()

    def add_output(self, output: str) -> None:
        max_width = self.style.width
        for line in output.splitlines():
            # Wrap long lines
            if len(line) > max_width:
                while len(line) > max_width:
                    self.state.lines.append(line[:max_width])
                    line = line[max_width:]
                if line:
                    self.state.lines.append(line)
            else:
                self.state.lines.append(line)
        # Add blank line after output for readability
        if output:
            self.state.lines.append("")
        self.state.current_line = self.state.prompt

    def execute_command(self, cmd: str) -> str:
        if not cmd or cmd.startswith("#"):
            return ""
        try:
            import sys
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.state.cwd,
                env={**os.environ, "FORCE_COLOR": "0", "NO_COLOR": "1", "TERM": "dumb"},
                timeout=30,
                errors="replace",
            )
            output = result.stdout
            if result.stderr:
                output += result.stderr
            return output.rstrip()
        except subprocess.TimeoutExpired:
            return "[Command timed out]"
        except Exception as e:
            return f"[Error: {e}]"

    def _draw_window_chrome(self, draw: ImageDraw.ImageDraw, x: int, y: int, width: int):
        """Draw macOS-style title bar."""
        s = self.style
        scale = s.scale
        colors = self.colors

        # Scaled dimensions
        title_h = s.title_bar_height * scale
        btn_r = s.button_radius * scale
        btn_spacing = s.button_spacing * scale
        pad = s.padding * scale

        # Divider line
        line_y = y + title_h
        draw.line([(x, line_y), (x + width, line_y)], fill=colors["surface1"], width=scale)

        # Traffic light buttons
        btn_y = y + title_h // 2
        btn_x = x + pad + btn_r

        for color in ["red", "yellow", "green"]:
            draw.ellipse(
                [btn_x - btn_r, btn_y - btn_r, btn_x + btn_r, btn_y + btn_r],
                fill=colors[color]
            )
            btn_x += btn_r * 2 + btn_spacing

        # Title text (centered)
        title = s.title
        title_bbox = self.title_font.getbbox(title)
        title_w = title_bbox[2] - title_bbox[0]
        title_x = x + (width - title_w) // 2
        title_y = y + (title_h - (title_bbox[3] - title_bbox[1])) // 2
        draw.text((title_x, title_y), title, font=self.title_font, fill=colors["subtext0"])

    def _resolve_color(self, color_name: str, is_foreground: bool = True) -> str:
        """Resolve an ANSI color name or hex color to a theme color or hex.

        Args:
            color_name: Color name (e.g., "red", "green", "text") or hex ("#rrggbb")
            is_foreground: Whether this is a foreground color (affects defaults)

        Returns:
            Hex color string
        """
        # Already hex color
        if color_name.startswith("#"):
            return color_name

        # Map ANSI color names to theme colors
        ansi_to_theme = {
            # Standard ANSI colors
            "black": "crust",
            "red": "red",
            "green": "green",
            "yellow": "yellow",
            "blue": "blue",
            "magenta": "mauve",
            "cyan": "teal",
            "white": "text",
            # Bright ANSI colors
            "bright_black": "surface2",
            "bright_red": "red",
            "bright_green": "green",
            "bright_yellow": "yellow",
            "bright_blue": "blue",
            "bright_magenta": "mauve",
            "bright_cyan": "teal",
            "bright_white": "text",
            # Default names
            "text": "text",
            "base": "base",
        }

        theme_key = ansi_to_theme.get(color_name, "text" if is_foreground else "base")
        return self.colors.get(theme_key, self.colors["text"] if is_foreground else self.colors["base"])

    def _draw_styled_line(self, draw: ImageDraw.ImageDraw, cells: list[StyledCell], x: int, y: int):
        """Draw a line with per-character styling (for native TUI colors)."""
        for cell in cells:
            if cell.char.strip():  # Only draw non-whitespace or draw all
                fg_color = self._resolve_color(cell.fg, is_foreground=True)
                # TODO: Background colors could be drawn as rectangles if needed
                draw.text((x, y), cell.char, font=self.font, fill=fg_color)
            x += self.char_width

    def _draw_text_line(self, draw: ImageDraw.ImageDraw, line: str, x: int, y: int):
        """Draw a line with syntax highlighting."""
        prompt = self.state.prompt
        colors = self.colors

        if line.startswith(prompt) and prompt:
            parts = prompt.split("@")
            if len(parts) == 2:
                user = parts[0]
                rest = "@" + parts[1]

                # Username in green
                draw.text((x, y), user, font=self.font, fill=colors["green"])
                x += len(user) * self.char_width

                # @path in blue
                path_part = rest.split(" $ ")[0]
                draw.text((x, y), path_part, font=self.font, fill=colors["blue"])
                x += len(path_part) * self.char_width

                # $ in lavender
                draw.text((x, y), " $ ", font=self.font, fill=colors["lavender"])
                x += 3 * self.char_width

                # Command in bright text
                cmd = line[len(prompt):]
                draw.text((x, y), cmd, font=self.font, fill=colors["text"])
            else:
                # Custom prompt - draw prompt in lavender, command in text
                draw.text((x, y), prompt, font=self.font, fill=colors["lavender"])
                x += len(prompt) * self.char_width
                cmd = line[len(prompt):]
                draw.text((x, y), cmd, font=self.font, fill=colors["text"])
        else:
            # Output in slightly dimmer text
            draw.text((x, y), line, font=self.font, fill=colors["subtext1"])

    def render(self) -> Image.Image:
        """Render terminal to high-quality image."""
        s = self.style
        scale = s.scale
        colors = self.colors

        # Calculate scaled sizes
        content_w = s.width * self.char_width
        content_h = s.height * self.char_height
        pad = s.padding * scale

        if s.chrome:
            title_h = s.title_bar_height * scale
            corner_r = s.corner_radius * scale
            margin = s.shadow_blur * scale
        else:
            title_h = 0
            corner_r = 8 * scale
            margin = 4 * scale

        window_w = content_w + pad * 2
        window_h = content_h + title_h + pad * 2

        canvas_w = window_w + margin * 2
        canvas_h = window_h + margin * 2

        canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        window_x = margin
        window_y = margin

        if s.chrome:
            shadow = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow)

            shadow_offset_x = 4 * scale
            shadow_offset_y = 8 * scale
            shadow_x = margin + shadow_offset_x
            shadow_y = margin + shadow_offset_y
            shadow_draw.rounded_rectangle(
                [shadow_x, shadow_y, shadow_x + window_w, shadow_y + window_h],
                radius=corner_r,
                fill=(0, 0, 0, 100)
            )

            shadow = shadow.filter(ImageFilter.GaussianBlur(radius=s.shadow_blur * scale // 2))
            canvas.paste(shadow, (0, 0), shadow)
            draw = ImageDraw.Draw(canvas)

            glow_size = 2 * scale
            draw.rounded_rectangle(
                [window_x - glow_size, window_y - glow_size,
                 window_x + window_w + glow_size, window_y + window_h + glow_size],
                radius=corner_r + glow_size,
                fill=colors["surface0"]
            )

        draw.rounded_rectangle(
            [window_x, window_y, window_x + window_w, window_y + window_h],
            radius=corner_r,
            fill=colors["base"]
        )

        if s.chrome:
            inner_shadow_y = window_y + title_h
            for i in range(6):
                alpha = 30 - i * 5
                if alpha > 0:
                    y_pos = inner_shadow_y + i * scale
                    draw.line(
                        [(window_x + corner_r, y_pos), (window_x + window_w - corner_r, y_pos)],
                        fill=(*hex_to_rgb(colors["crust"]), alpha),
                        width=scale
                    )
            self._draw_window_chrome(draw, window_x, window_y, window_w)

        content_x = window_x + pad
        content_y = window_y + title_h + pad

        # Check if we have styled lines (native color mode)
        visible_line_count = 0
        if self.state.styled_lines is not None:
            visible_styled = self.state.styled_lines[-s.height:]
            visible_line_count = len(visible_styled)
            y = content_y
            for cells in visible_styled:
                # Truncate if too long
                if len(cells) > s.width:
                    cells = cells[:s.width - 1] + [StyledCell(char="…")]
                self._draw_styled_line(draw, cells, content_x, y)
                y += self.char_height
        else:
            all_lines = self.state.lines + [self.state.current_line]
            visible_lines = all_lines[-s.height:]
            visible_line_count = len(visible_lines)

            y = content_y
            for line in visible_lines:
                if len(line) > s.width:
                    line = line[:s.width - 1] + "…"
                self._draw_text_line(draw, line, content_x, y)
                y += self.char_height

        # Draw cursor based on style (skip in native/TUI mode - TUI apps manage their own cursor)
        if self.state.styled_lines is None and visible_line_count > 0:
            cursor_line_idx = visible_line_count - 1
            cursor_x = content_x + len(self.state.current_line) * self.char_width
            cursor_y = content_y + cursor_line_idx * self.char_height

            if s.cursor == "block":
                cursor_h = self.char_height - 4 * scale
                draw.rounded_rectangle(
                    [cursor_x, cursor_y + 2 * scale,
                     cursor_x + self.char_width - 2 * scale, cursor_y + cursor_h],
                    radius=2 * scale,
                    fill=colors["lavender"]
                )
            elif s.cursor == "bar":
                draw.rectangle(
                    [cursor_x, cursor_y + 2 * scale,
                     cursor_x + 2 * scale, cursor_y + self.char_height - 2 * scale],
                    fill=colors["lavender"]
                )
            elif s.cursor == "underline":
                draw.rectangle(
                    [cursor_x, cursor_y + self.char_height - 4 * scale,
                     cursor_x + self.char_width - 2 * scale, cursor_y + self.char_height - 2 * scale],
                    fill=colors["lavender"]
                )

        final_w = canvas_w // scale
        final_h = canvas_h // scale
        canvas = canvas.resize((final_w, final_h), Image.LANCZOS)

        bg_color = hex_to_rgb(colors["base"] if not s.chrome else colors["mantle"])
        result = Image.new("RGB", (final_w, final_h), bg_color)
        result.paste(canvas, (0, 0), canvas)

        # Apply rounded corners to the outer edge of the final image
        if s.outer_radius > 0:
            mask = create_rounded_rectangle_mask((final_w, final_h), s.outer_radius)
            # Create background for corners (dark color that looks good)
            corner_bg = Image.new("RGB", (final_w, final_h), hex_to_rgb(colors["crust"]))
            result = Image.composite(result, corner_bg, mask)

        return result
