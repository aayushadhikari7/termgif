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
            code = ord(char)

            # Escape sequence
            if char == '\x1b':
                # Try to parse escape sequence
                seq_match = self._parse_escape(data[i:])
                if seq_match:
                    seq, length = seq_match
                    self._handle_escape(seq)
                    i += length
                    continue
                # Standalone ESC - skip it
                i += 1
                continue

            # Control characters (0x00-0x1F and 0x7F)
            if code < 32 or code == 127:
                if char == '\n':
                    self.newline()
                elif char == '\r':
                    self.carriage_return()
                elif char == '\t':
                    self.tab()
                elif char == '\b':
                    self.backspace()
                # All other control chars (bell, etc.) are ignored
                i += 1
                continue

            # C1 control characters (0x80-0x9F) - skip them
            if 0x80 <= code <= 0x9F:
                i += 1
                continue

            # Printable character (0x20-0x7E, or extended unicode)
            self.write_char(char)
            i += 1

    def _parse_escape(self, data: str) -> tuple | None:
        """Parse escape sequence, return (sequence, length) or None.

        This parser is designed to ALWAYS consume escape sequences fully,
        never allowing partial sequences to leak as visible characters.
        """
        if len(data) < 2:
            # Incomplete - consume just the ESC to prevent it showing
            return (('INCOMPLETE',), 1)

        second = data[1]

        # CSI sequences: ESC [ (Control Sequence Introducer)
        if second == '[':
            # Find end: final byte is 0x40-0x7E (@, A-Z, [\]^_`, a-z, {|}~)
            for j in range(2, min(len(data), 256)):
                c = data[j]
                code = ord(c)
                if 0x40 <= code <= 0x7E:  # Final byte
                    params_str = data[2:j]
                    params_clean = ''.join(ch for ch in params_str if ch in '0123456789;?:<=>')
                    return (('CSI', params_clean, c), j + 1)
                elif code < 0x20:  # Control char - sequence is malformed
                    break
            # Consume ESC [ at minimum
            return (('MALFORMED',), 2)

        # OSC sequences: ESC ] (Operating System Command) - titles, colors, etc.
        if second == ']':
            return self._parse_string_sequence(data, 2)

        # DCS sequences: ESC P (Device Control String)
        if second == 'P':
            return self._parse_string_sequence(data, 2)

        # SOS, PM, APC: ESC X, ESC ^, ESC _
        if second in 'X^_':
            return self._parse_string_sequence(data, 2)

        # Character set: ESC ( X, ESC ) X, ESC * X, ESC + X, ESC - X, ESC . X, ESC / X
        if second in '()*+-./':
            if len(data) >= 3:
                return (('CHARSET',), 3)
            return (('INCOMPLETE',), 2)

        # Two-character sequences
        two_char_seqs = {
            '7': 'SAVE_CURSOR', '8': 'RESTORE_CURSOR',
            'c': 'RESET', 'D': 'INDEX', 'E': 'NEXT_LINE', 'H': 'TAB_SET',
            'M': 'REVERSE_INDEX', 'N': 'SS2', 'O': 'SS3',
            '=': 'KEYPAD_APP', '>': 'KEYPAD_NUM',
            '\\': 'ST', 'Z': 'DECID',
            # Less common but valid
            '6': 'DECBI', '9': 'DECFI', 'F': 'CURSOR_LOWER_LEFT',
            'l': 'MEMORY_LOCK', 'm': 'MEMORY_UNLOCK',
            'n': 'LS2', 'o': 'LS3', '|': 'LS3R', '}': 'LS2R', '~': 'LS1R',
        }
        if second in two_char_seqs:
            return ((two_char_seqs[second],), 2)

        # Space + letter sequences: ESC SP F, ESC SP G, etc.
        if second == ' ':
            if len(data) >= 3:
                return (('SPACE_SEQ',), 3)
            return (('INCOMPLETE',), 2)

        # Hash sequences: ESC # 3, ESC # 8, etc.
        if second == '#':
            if len(data) >= 3:
                return (('HASH_SEQ',), 3)
            return (('INCOMPLETE',), 2)

        # Percent sequences: ESC % @, ESC % G, etc. (character set)
        if second == '%':
            if len(data) >= 3:
                return (('PERCENT_SEQ',), 3)
            return (('INCOMPLETE',), 2)

        # Any other printable after ESC - consume as 2-byte unknown
        if 0x20 <= ord(second) <= 0x7E:
            return (('UNKNOWN',), 2)

        # Non-printable after ESC - just consume ESC
        return (('UNKNOWN',), 1)

    def _parse_string_sequence(self, data: str, start: int) -> tuple:
        """Parse a string sequence (OSC, DCS, etc.) that ends with ST or BEL."""
        # Look for terminator: BEL (\x07) or ST (\x1b\\ or \x9c)
        for j in range(start, min(len(data), 8192)):
            c = data[j]
            if c == '\x07':  # BEL terminator
                return (('STRING_SEQ',), j + 1)
            if c == '\x9c':  # C1 ST
                return (('STRING_SEQ',), j + 1)
            if c == '\x1b' and j + 1 < len(data) and data[j + 1] == '\\':
                return (('STRING_SEQ',), j + 2)
        # No terminator found - consume the introducer only
        return (('INCOMPLETE',), start)

    def _handle_escape(self, seq: tuple):
        """Handle parsed escape sequence."""
        seq_type = seq[0]

        if seq_type == 'CSI':
            params_str, cmd = seq[1], seq[2]
            # Remove '?' prefix for private sequences
            is_private = params_str.startswith('?')
            clean_params = params_str.lstrip('?')
            params = []
            if clean_params:
                for p in clean_params.split(';'):
                    try:
                        params.append(int(p) if p else 0)
                    except ValueError:
                        params.append(0)

            if cmd == 'A':  # Cursor up
                self.move_cursor('up', params[0] if params else 1)
            elif cmd == 'B':  # Cursor down
                self.move_cursor('down', params[0] if params else 1)
            elif cmd == 'C':  # Cursor forward
                self.move_cursor('right', params[0] if params else 1)
            elif cmd == 'D':  # Cursor back
                self.move_cursor('left', params[0] if params else 1)
            elif cmd == 'E':  # Cursor next line
                self.cursor_x = 0
                self.move_cursor('down', params[0] if params else 1)
            elif cmd == 'F':  # Cursor previous line
                self.cursor_x = 0
                self.move_cursor('up', params[0] if params else 1)
            elif cmd == 'G':  # Cursor horizontal absolute
                col = params[0] if params else 1
                self.cursor_x = max(0, min(self.width - 1, col - 1))
            elif cmd == 'H' or cmd == 'f':  # Cursor position
                row = params[0] if params else 1
                col = params[1] if len(params) > 1 else 1
                self.set_cursor(row, col)
            elif cmd == 'J':  # Erase display
                self.clear_screen(params[0] if params else 0)
            elif cmd == 'K':  # Erase line
                self.clear_line(params[0] if params else 0)
            elif cmd == 'L':  # Insert lines
                pass  # TODO: implement if needed
            elif cmd == 'M':  # Delete lines
                pass  # TODO: implement if needed
            elif cmd == 'P':  # Delete characters
                pass  # TODO: implement if needed
            elif cmd == 'S':  # Scroll up
                count = params[0] if params else 1
                for _ in range(count):
                    self._scroll_up()
            elif cmd == 'T':  # Scroll down
                count = params[0] if params else 1
                for _ in range(count):
                    self._scroll_down()
            elif cmd == 'X':  # Erase characters
                count = params[0] if params else 1
                for x in range(self.cursor_x, min(self.cursor_x + count, self.width)):
                    self.screen[self.cursor_y][x] = Cell()
            elif cmd == 'd':  # Line position absolute
                row = params[0] if params else 1
                self.cursor_y = max(0, min(self.height - 1, row - 1))
            elif cmd == 'm':  # SGR (colors/attributes)
                self.set_sgr(params)
            elif cmd == 'n':  # Device status report - ignore
                pass
            elif cmd == 'r':  # Set scrolling region - ignore for now
                pass
            elif cmd == 's':  # Save cursor
                self.save_cursor()
            elif cmd == 't':  # Window manipulation - ignore
                pass
            elif cmd == 'u':  # Restore cursor
                self.restore_cursor()
            elif cmd == 'h':  # Set mode
                if is_private:
                    if 1049 in params:
                        self.enter_alt_screen()
                    # Other private modes (cursor visibility, mouse, etc.) - ignore
            elif cmd == 'l':  # Reset mode
                if is_private:
                    if 1049 in params:
                        self.exit_alt_screen()
                    # Other private modes - ignore
            elif cmd == 'c':  # Device attributes - ignore
                pass
            elif cmd == 'q':  # Cursor style - ignore
                pass
            # All other CSI commands are silently ignored

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
        elif seq_type == 'NEXT_LINE':
            self.cursor_x = 0
            self.cursor_y += 1
            if self.cursor_y >= self.height:
                self._scroll_up()
                self.cursor_y = self.height - 1
        # All other sequence types (OSC, DCS, CHARSET, UNKNOWN, etc.) are silently ignored

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
