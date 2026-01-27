"""Terminal renderer - high quality terminal screenshots."""
from PIL import Image, ImageDraw, ImageFilter
import subprocess
import os

from .themes import THEMES, resolve_color
from .fonts import get_font
from .styles import TerminalStyle, TerminalState, StyledCell, hex_to_rgb, create_rounded_rectangle_mask


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

        # Apply custom user/hostname/symbol if specified (before custom prompt)
        if s.user or s.hostname or s.symbol != "$":
            self.state.custom_user = s.user
            self.state.custom_hostname = s.hostname
            self.state.custom_symbol = s.symbol
            self.state._update_prompt()
            self.state.current_line = self.state.prompt

        # Apply custom prompt if specified (overrides user/hostname)
        if s.prompt:
            self.state.prompt = s.prompt
            self.state.current_line = s.prompt

        # Calculate character dimensions at scaled size
        bbox = self.font.getbbox("M")
        self.char_width = bbox[2] - bbox[0]
        self.char_height = int((bbox[3] - bbox[1]) * s.line_height)

    def type_char(self, char: str) -> None:
        """Type a single character."""
        self.state.current_line += char

    def type_text(self, text: str) -> None:
        """Type multiple characters."""
        for char in text:
            self.type_char(char)

    def press_enter(self) -> str:
        """Press enter and return the command typed."""
        self.state.lines.append(self.state.current_line)
        cmd = self.state.current_line
        if self.state.prompt and cmd.startswith(self.state.prompt):
            cmd = cmd[len(self.state.prompt):]
        self.state.current_line = ""
        return cmd.strip()

    def add_output(self, output: str) -> None:
        """Add command output to the terminal."""
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
        """Execute a shell command and return output."""
        if not cmd or cmd.startswith("#"):
            return ""
        try:
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
        """Resolve a color name to hex color."""
        return resolve_color(color_name, self.colors, is_foreground)

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

                # Find the symbol (last non-space word before command)
                # Format: @hostname symbol  (e.g., "@folder $ " or "@server # ")
                symbol = self.state.custom_symbol or "$"
                symbol_with_space = f" {symbol} "

                if symbol_with_space in rest:
                    path_part = rest.split(symbol_with_space)[0]
                    draw.text((x, y), path_part, font=self.font, fill=colors["blue"])
                    x += len(path_part) * self.char_width

                    # Symbol in lavender
                    draw.text((x, y), symbol_with_space, font=self.font, fill=colors["lavender"])
                    x += len(symbol_with_space) * self.char_width
                else:
                    # Fallback: draw rest in blue
                    draw.text((x, y), rest, font=self.font, fill=colors["blue"])
                    x += len(rest) * self.char_width

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

    def render_lines(self, lines: list[str]) -> Image.Image:
        """Render given lines to an image (for external data like asciinema).

        Args:
            lines: List of strings to render

        Returns:
            Rendered PIL Image
        """
        # Save current state
        old_lines = self.state.lines
        old_current = self.state.current_line

        # Set lines and render
        self.state.lines = lines[:-1] if lines else []
        self.state.current_line = lines[-1] if lines else ""

        result = self.render()

        # Restore state
        self.state.lines = old_lines
        self.state.current_line = old_current

        return result

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
