"""Simple VT100/ANSI terminal emulator for TUI capture."""
import re
from dataclasses import dataclass, field


@dataclass
class Cell:
    """A single cell in the terminal screen."""
    char: str = " "
    fg: str = "text"      # Foreground color name or RGB
    bg: str = "base"      # Background color name or RGB
    bold: bool = False
    dim: bool = False
    italic: bool = False
    underline: bool = False
    reverse: bool = False


@dataclass
class TerminalEmulator:
    """Simple VT100/ANSI terminal emulator.

    Parses escape sequences and maintains a screen buffer that can be
    rendered with our custom renderer.
    """
    width: int = 80
    height: int = 24

    # Cursor position (0-indexed)
    cursor_x: int = 0
    cursor_y: int = 0

    # Screen buffer
    screen: list = field(default_factory=list)

    # Current text attributes
    current_fg: str = "text"
    current_bg: str = "base"
    current_bold: bool = False
    current_dim: bool = False
    current_italic: bool = False
    current_underline: bool = False
    current_reverse: bool = False

    # Alternate screen buffer (for TUI apps)
    main_screen: list = None
    using_alt_screen: bool = False

    # Saved cursor position
    saved_cursor: tuple = (0, 0)

    def __post_init__(self):
        """Initialize screen buffer."""
        self._init_screen()

    def _init_screen(self):
        """Create empty screen buffer."""
        self.screen = [
            [Cell() for _ in range(self.width)]
            for _ in range(self.height)
        ]

    def _make_cell(self) -> Cell:
        """Create a cell with current attributes."""
        return Cell(
            char=" ",
            fg=self.current_fg,
            bg=self.current_bg,
            bold=self.current_bold,
            dim=self.current_dim,
            italic=self.current_italic,
            underline=self.current_underline,
            reverse=self.current_reverse,
        )

    def _scroll_up(self):
        """Scroll screen up by one line."""
        self.screen.pop(0)
        self.screen.append([Cell() for _ in range(self.width)])

    def _scroll_down(self):
        """Scroll screen down by one line."""
        self.screen.pop()
        self.screen.insert(0, [Cell() for _ in range(self.width)])

    def write_char(self, char: str):
        """Write a single character at cursor position."""
        if self.cursor_x >= self.width:
            # Wrap to next line
            self.cursor_x = 0
            self.cursor_y += 1

        if self.cursor_y >= self.height:
            # Scroll up
            self._scroll_up()
            self.cursor_y = self.height - 1

        # Write character
        cell = self._make_cell()
        cell.char = char
        self.screen[self.cursor_y][self.cursor_x] = cell
        self.cursor_x += 1

    def newline(self):
        """Handle newline."""
        self.cursor_x = 0
        self.cursor_y += 1
        if self.cursor_y >= self.height:
            self._scroll_up()
            self.cursor_y = self.height - 1

    def carriage_return(self):
        """Handle carriage return."""
        self.cursor_x = 0

    def backspace(self):
        """Handle backspace."""
        if self.cursor_x > 0:
            self.cursor_x -= 1

    def tab(self):
        """Handle tab."""
        # Move to next tab stop (every 8 columns)
        self.cursor_x = ((self.cursor_x // 8) + 1) * 8
        if self.cursor_x >= self.width:
            self.cursor_x = self.width - 1

    def clear_screen(self, mode: int = 2):
        """Clear screen. mode: 0=below, 1=above, 2=all, 3=all+scrollback."""
        if mode == 0:
            # Clear from cursor to end
            for x in range(self.cursor_x, self.width):
                self.screen[self.cursor_y][x] = Cell()
            for y in range(self.cursor_y + 1, self.height):
                self.screen[y] = [Cell() for _ in range(self.width)]
        elif mode == 1:
            # Clear from start to cursor
            for y in range(self.cursor_y):
                self.screen[y] = [Cell() for _ in range(self.width)]
            for x in range(self.cursor_x + 1):
                self.screen[self.cursor_y][x] = Cell()
        else:
            # Clear all
            self._init_screen()

    def clear_line(self, mode: int = 2):
        """Clear line. mode: 0=to end, 1=to start, 2=all."""
        if mode == 0:
            for x in range(self.cursor_x, self.width):
                self.screen[self.cursor_y][x] = Cell()
        elif mode == 1:
            for x in range(self.cursor_x + 1):
                self.screen[self.cursor_y][x] = Cell()
        else:
            self.screen[self.cursor_y] = [Cell() for _ in range(self.width)]

    def set_cursor(self, row: int, col: int):
        """Set cursor position (1-indexed input, converted to 0-indexed)."""
        self.cursor_y = max(0, min(self.height - 1, row - 1))
        self.cursor_x = max(0, min(self.width - 1, col - 1))

    def move_cursor(self, direction: str, count: int = 1):
        """Move cursor in direction by count."""
        if direction == "up":
            self.cursor_y = max(0, self.cursor_y - count)
        elif direction == "down":
            self.cursor_y = min(self.height - 1, self.cursor_y + count)
        elif direction == "left":
            self.cursor_x = max(0, self.cursor_x - count)
        elif direction == "right":
            self.cursor_x = min(self.width - 1, self.cursor_x + count)

    def save_cursor(self):
        """Save cursor position."""
        self.saved_cursor = (self.cursor_x, self.cursor_y)

    def restore_cursor(self):
        """Restore cursor position."""
        self.cursor_x, self.cursor_y = self.saved_cursor

    def enter_alt_screen(self):
        """Switch to alternate screen buffer."""
        if not self.using_alt_screen:
            self.main_screen = self.screen
            self._init_screen()
            self.using_alt_screen = True

    def exit_alt_screen(self):
        """Switch back to main screen buffer."""
        if self.using_alt_screen and self.main_screen:
            self.screen = self.main_screen
            self.main_screen = None
            self.using_alt_screen = False

    def set_sgr(self, params: list):
        """Set Select Graphic Rendition (colors and attributes)."""
        if not params:
            params = [0]

        i = 0
        while i < len(params):
            p = params[i]

            if p == 0:
                # Reset all
                self.current_fg = "text"
                self.current_bg = "base"
                self.current_bold = False
                self.current_dim = False
                self.current_italic = False
                self.current_underline = False
                self.current_reverse = False
            elif p == 1:
                self.current_bold = True
            elif p == 2:
                self.current_dim = True
            elif p == 3:
                self.current_italic = True
            elif p == 4:
                self.current_underline = True
            elif p == 7:
                self.current_reverse = True
            elif p == 22:
                self.current_bold = False
                self.current_dim = False
            elif p == 23:
                self.current_italic = False
            elif p == 24:
                self.current_underline = False
            elif p == 27:
                self.current_reverse = False
            # Foreground colors (30-37, 90-97)
            elif 30 <= p <= 37:
                self.current_fg = self._ansi_color(p - 30)
            elif 90 <= p <= 97:
                self.current_fg = self._ansi_color(p - 90 + 8)
            elif p == 39:
                self.current_fg = "text"
            # Background colors (40-47, 100-107)
            elif 40 <= p <= 47:
                self.current_bg = self._ansi_color(p - 40)
            elif 100 <= p <= 107:
                self.current_bg = self._ansi_color(p - 100 + 8)
            elif p == 49:
                self.current_bg = "base"
            # 256 color (38;5;n or 48;5;n)
            elif p == 38 and i + 2 < len(params) and params[i + 1] == 5:
                self.current_fg = self._256_color(params[i + 2])
                i += 2
            elif p == 48 and i + 2 < len(params) and params[i + 1] == 5:
                self.current_bg = self._256_color(params[i + 2])
                i += 2
            # True color (38;2;r;g;b or 48;2;r;g;b)
            elif p == 38 and i + 4 < len(params) and params[i + 1] == 2:
                r, g, b = params[i + 2], params[i + 3], params[i + 4]
                self.current_fg = f"#{r:02x}{g:02x}{b:02x}"
                i += 4
            elif p == 48 and i + 4 < len(params) and params[i + 1] == 2:
                r, g, b = params[i + 2], params[i + 3], params[i + 4]
                self.current_bg = f"#{r:02x}{g:02x}{b:02x}"
                i += 4

            i += 1

    def _ansi_color(self, n: int) -> str:
        """Convert ANSI color number to color name."""
        colors = [
            "black", "red", "green", "yellow",
            "blue", "magenta", "cyan", "white",
            "bright_black", "bright_red", "bright_green", "bright_yellow",
            "bright_blue", "bright_magenta", "bright_cyan", "bright_white",
        ]
        return colors[n] if n < len(colors) else "text"

    def _256_color(self, n: int) -> str:
        """Convert 256 color number to hex color."""
        if n < 16:
            return self._ansi_color(n)
        elif n < 232:
            # 6x6x6 color cube
            n -= 16
            r = (n // 36) * 51
            g = ((n // 6) % 6) * 51
            b = (n % 6) * 51
            return f"#{r:02x}{g:02x}{b:02x}"
        else:
            # Grayscale
            g = (n - 232) * 10 + 8
            return f"#{g:02x}{g:02x}{g:02x}"

    def feed(self, data: str):
        """Process input data (text + escape sequences)."""
        i = 0
        while i < len(data):
            char = data[i]

            # Escape sequence
            if char == '\x1b':
                # Try to parse escape sequence
                seq_match = self._parse_escape(data[i:])
                if seq_match:
                    seq, length = seq_match
                    self._handle_escape(seq)
                    i += length
                    continue

            # Control characters
            if char == '\n':
                self.newline()
            elif char == '\r':
                self.carriage_return()
            elif char == '\t':
                self.tab()
            elif char == '\b':
                self.backspace()
            elif char == '\x07':
                pass  # Bell - ignore
            elif ord(char) >= 32:
                # Printable character
                self.write_char(char)

            i += 1

    def _parse_escape(self, data: str) -> tuple | None:
        """Parse escape sequence, return (sequence, length) or None."""
        if len(data) < 2:
            return None

        # CSI sequences: ESC [
        if data[1] == '[':
            # Find end of CSI sequence
            match = re.match(r'\x1b\[([0-9;?]*)([A-Za-z@`])', data)
            if match:
                return (('CSI', match.group(1), match.group(2)), match.end())

        # OSC sequences: ESC ]
        elif data[1] == ']':
            # Find terminator (BEL or ST)
            end = data.find('\x07', 2)
            if end == -1:
                end = data.find('\x1b\\', 2)
            if end != -1:
                return (('OSC', data[2:end]), end + 1)

        # Simple sequences
        elif data[1] == '7':
            return (('SAVE_CURSOR',), 2)
        elif data[1] == '8':
            return (('RESTORE_CURSOR',), 2)
        elif data[1] == 'c':
            return (('RESET',), 2)
        elif data[1] == 'M':
            return (('REVERSE_INDEX',), 2)
        elif data[1] == 'D':
            return (('INDEX',), 2)

        return None

    def _handle_escape(self, seq: tuple):
        """Handle parsed escape sequence."""
        seq_type = seq[0]

        if seq_type == 'CSI':
            params_str, cmd = seq[1], seq[2]
            params = [int(p) if p else 0 for p in params_str.split(';')] if params_str else []

            if cmd == 'A':  # Cursor up
                self.move_cursor('up', params[0] if params else 1)
            elif cmd == 'B':  # Cursor down
                self.move_cursor('down', params[0] if params else 1)
            elif cmd == 'C':  # Cursor forward
                self.move_cursor('right', params[0] if params else 1)
            elif cmd == 'D':  # Cursor back
                self.move_cursor('left', params[0] if params else 1)
            elif cmd == 'H' or cmd == 'f':  # Cursor position
                row = params[0] if params else 1
                col = params[1] if len(params) > 1 else 1
                self.set_cursor(row, col)
            elif cmd == 'J':  # Erase display
                self.clear_screen(params[0] if params else 0)
            elif cmd == 'K':  # Erase line
                self.clear_line(params[0] if params else 0)
            elif cmd == 'm':  # SGR (colors/attributes)
                self.set_sgr(params)
            elif cmd == 's':  # Save cursor
                self.save_cursor()
            elif cmd == 'u':  # Restore cursor
                self.restore_cursor()
            elif cmd == 'h':  # Set mode
                if params_str == '?1049':
                    self.enter_alt_screen()
                elif params_str == '?25':
                    pass  # Show cursor - ignore
            elif cmd == 'l':  # Reset mode
                if params_str == '?1049':
                    self.exit_alt_screen()
                elif params_str == '?25':
                    pass  # Hide cursor - ignore

        elif seq_type == 'SAVE_CURSOR':
            self.save_cursor()
        elif seq_type == 'RESTORE_CURSOR':
            self.restore_cursor()
        elif seq_type == 'RESET':
            self.__post_init__()
        elif seq_type == 'INDEX':
            self.cursor_y += 1
            if self.cursor_y >= self.height:
                self._scroll_up()
                self.cursor_y = self.height - 1
        elif seq_type == 'REVERSE_INDEX':
            self.cursor_y -= 1
            if self.cursor_y < 0:
                self._scroll_down()
                self.cursor_y = 0

    def get_lines(self) -> list[str]:
        """Get screen content as list of strings (for simple rendering)."""
        lines = []
        for row in self.screen:
            line = ''.join(cell.char for cell in row).rstrip()
            lines.append(line)
        return lines

    def get_screen(self) -> list[list[Cell]]:
        """Get full screen buffer with attributes."""
        return self.screen
