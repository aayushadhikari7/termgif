"""Parser for .tg (termgif script) format.

Syntax:
    @output "file.gif"      - Set output path
    @size 80x24             - Set terminal dimensions
    @font 14                - Set font size
    @speed 50ms             - Set typing speed
    @title "Demo"           - Set window title
    @loop 0                 - Set loop count (0=infinite)
    @quality 2              - Render scale (1-3)
    @bare                   - No window chrome
    @fps 15                 - Frames per second
    @theme "dracula"        - Color theme
    @padding 20             - Padding around content
    @prompt "$ "            - Custom shell prompt
    @cursor "bar"           - Cursor style (block/bar/underline)
    @start 500ms            - Initial delay
    @end 2s                 - Final frame hold
    @radius 10              - Corner radius in pixels (0 = sharp)

    -> "text"               - Type text
    >>                      - Press enter
    ~500ms                  - Sleep
    -> "text" >>            - Type + enter (combined)
    key "escape"            - Press special key (for TUI apps)
    key "ctrl+c"            - Press key combo (ctrl, alt modifiers)

    // comment              - Single-line comment
    /* comment */           - Multi-line comment

Supported keys for TUI interaction:
    Navigation: up, down, left, right, home, end, pageup, pagedown
    Editing: backspace, delete, tab, space
    Control: escape, enter, return
    Modifiers: ctrl+c, ctrl+d, ctrl+z, ctrl+l, alt+<key>
    Function keys: f1-f12
"""
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Iterator

from .tape import TapeConfig, TypeAction, EnterAction, SleepAction, KeyAction, parse_duration


class TokenType(Enum):
    """Token types for .tg format."""
    # Configuration directives
    AT_OUTPUT = auto()
    AT_SIZE = auto()
    AT_FONT = auto()
    AT_SPEED = auto()
    AT_LOOP = auto()
    AT_TITLE = auto()
    AT_QUALITY = auto()
    AT_BARE = auto()
    AT_FPS = auto()
    AT_THEME = auto()
    AT_PADDING = auto()
    AT_PROMPT = auto()
    AT_CURSOR = auto()
    AT_START = auto()
    AT_END = auto()
    AT_RADIUS = auto()
    AT_RADIUS_OUTER = auto()
    AT_RADIUS_INNER = auto()
    AT_NATIVE = auto()

    # Actions
    ARROW = auto()          # ->
    DOUBLE_ARROW = auto()   # >>
    TILDE = auto()          # ~ (with duration)
    KEY = auto()            # key "..." (special key press)

    # Values
    STRING = auto()
    DURATION = auto()
    DIMENSIONS = auto()
    NUMBER = auto()

    # Structure
    NEWLINE = auto()
    EOF = auto()


@dataclass
class Token:
    """A single token from the .tg file."""
    type: TokenType
    value: str
    line: int
    column: int


class TgTokenizer:
    """Tokenizer for .tg format."""

    def __init__(self, content: str):
        self.content = content
        self.pos = 0
        self.line = 1
        self.column = 1

    def _current(self) -> str:
        """Get current character."""
        if self.pos >= len(self.content):
            return ""
        return self.content[self.pos]

    def _peek(self, offset: int = 1) -> str:
        """Peek at character ahead."""
        pos = self.pos + offset
        if pos >= len(self.content):
            return ""
        return self.content[pos]

    def _advance(self) -> str:
        """Advance position and return current character."""
        char = self._current()
        self.pos += 1
        self.column += 1
        return char

    def _make_token(self, token_type: TokenType, value: str) -> Token:
        """Create a token at current position."""
        return Token(token_type, value, self.line, self.column)

    def _skip_line_comment(self) -> None:
        """Skip // comment until end of line."""
        while self._current() and self._current() != "\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        """Skip /* */ comment."""
        self._advance()  # skip /
        self._advance()  # skip *
        while self._current():
            if self._current() == "*" and self._peek() == "/":
                self._advance()  # skip *
                self._advance()  # skip /
                return
            if self._current() == "\n":
                self.line += 1
                self.column = 0
            self._advance()
        raise SyntaxError(f"Unterminated block comment at line {self.line}")

    def _read_string(self) -> Token:
        """Read a quoted string."""
        start_line = self.line
        start_col = self.column
        self._advance()  # skip opening quote

        chars = []
        while self._current() and self._current() != '"':
            if self._current() == "\\":
                self._advance()
                escape_char = self._current()
                if escape_char == "n":
                    chars.append("\n")
                elif escape_char == "t":
                    chars.append("\t")
                elif escape_char == "\\":
                    chars.append("\\")
                elif escape_char == '"':
                    chars.append('"')
                else:
                    chars.append(escape_char)
                self._advance()
            elif self._current() == "\n":
                raise SyntaxError(f"Unterminated string at line {start_line}")
            else:
                chars.append(self._advance())

        if not self._current():
            raise SyntaxError(f"Unterminated string at line {start_line}")

        self._advance()  # skip closing quote
        return Token(TokenType.STRING, "".join(chars), start_line, start_col)

    def _read_directive(self) -> Token:
        """Read an @ directive (supports hyphenated names like @radius-outer)."""
        start_col = self.column
        self._advance()  # skip @

        word = []
        while self._current() and (self._current().isalpha() or self._current() == "-"):
            word.append(self._advance())

        directive = "".join(word).lower()
        token_map = {
            "output": TokenType.AT_OUTPUT,
            "size": TokenType.AT_SIZE,
            "font": TokenType.AT_FONT,
            "speed": TokenType.AT_SPEED,
            "loop": TokenType.AT_LOOP,
            "title": TokenType.AT_TITLE,
            "quality": TokenType.AT_QUALITY,
            "bare": TokenType.AT_BARE,
            "fps": TokenType.AT_FPS,
            "theme": TokenType.AT_THEME,
            "padding": TokenType.AT_PADDING,
            "prompt": TokenType.AT_PROMPT,
            "cursor": TokenType.AT_CURSOR,
            "start": TokenType.AT_START,
            "end": TokenType.AT_END,
            "radius": TokenType.AT_RADIUS,
            "radius-outer": TokenType.AT_RADIUS_OUTER,
            "radius-inner": TokenType.AT_RADIUS_INNER,
            "native": TokenType.AT_NATIVE,
        }

        if directive not in token_map:
            raise SyntaxError(f"Unknown directive @{directive} at line {self.line}")

        return Token(token_map[directive], directive, self.line, start_col)

    def _read_duration(self) -> Token:
        """Read a duration value after ~."""
        start_col = self.column
        chars = []

        # Read number part (including decimal point)
        while self._current() and (self._current().isdigit() or self._current() == "."):
            chars.append(self._advance())

        # Read unit suffix (ms, s)
        while self._current() and self._current().isalpha():
            chars.append(self._advance())

        return Token(TokenType.DURATION, "".join(chars), self.line, start_col)

    def _read_number_or_dimensions(self) -> Token:
        """Read a number or dimensions (e.g., 80x24)."""
        start_col = self.column
        chars = []

        # Read first number
        while self._current() and self._current().isdigit():
            chars.append(self._advance())

        # Check for dimensions (80x24)
        if self._current() == "x" and self._peek().isdigit():
            chars.append(self._advance())  # x
            while self._current() and self._current().isdigit():
                chars.append(self._advance())
            return Token(TokenType.DIMENSIONS, "".join(chars), self.line, start_col)

        # Check for duration suffix
        if self._current() in ("m", "s"):
            while self._current() and self._current().isalpha():
                chars.append(self._advance())
            return Token(TokenType.DURATION, "".join(chars), self.line, start_col)

        return Token(TokenType.NUMBER, "".join(chars), self.line, start_col)

    def tokenize(self) -> Iterator[Token]:
        """Generate all tokens from the content."""
        while self.pos < len(self.content):
            # Skip whitespace (except newlines)
            if self._current() in " \t\r":
                self._advance()
                continue

            # Newline
            if self._current() == "\n":
                yield self._make_token(TokenType.NEWLINE, "\n")
                self._advance()
                self.line += 1
                self.column = 1
                continue

            # Comments
            if self._current() == "/" and self._peek() == "/":
                self._skip_line_comment()
                continue
            if self._current() == "/" and self._peek() == "*":
                self._skip_block_comment()
                continue

            # @ directives
            if self._current() == "@":
                yield self._read_directive()
                continue

            # -> arrow
            if self._current() == "-" and self._peek() == ">":
                yield self._make_token(TokenType.ARROW, "->")
                self._advance()
                self._advance()
                continue

            # >> double arrow
            if self._current() == ">" and self._peek() == ">":
                yield self._make_token(TokenType.DOUBLE_ARROW, ">>")
                self._advance()
                self._advance()
                continue

            # ~ tilde (for timing)
            if self._current() == "~":
                self._advance()
                yield self._read_duration()
                continue

            # String
            if self._current() == '"':
                yield self._read_string()
                continue

            # Number or dimensions
            if self._current().isdigit():
                yield self._read_number_or_dimensions()
                continue

            # Keywords (key)
            if self._current().isalpha():
                start_col = self.column
                word = []
                while self._current() and self._current().isalnum():
                    word.append(self._advance())
                keyword = "".join(word).lower()
                if keyword == "key":
                    yield Token(TokenType.KEY, "key", self.line, start_col)
                    continue
                else:
                    raise SyntaxError(
                        f"Unknown keyword '{keyword}' at line {self.line}, column {start_col}"
                    )

            raise SyntaxError(
                f"Unexpected character '{self._current()}' at line {self.line}, column {self.column}"
            )

        yield self._make_token(TokenType.EOF, "")


class TgParser:
    """Parser for .tg format."""

    def __init__(self, content: str):
        self.tokenizer = TgTokenizer(content)
        self.tokens: list[Token] = []
        self.pos = 0

    def _current(self) -> Token:
        """Get current token."""
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # EOF
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        """Advance and return current token."""
        token = self._current()
        self.pos += 1
        return token

    def _expect(self, token_type: TokenType) -> Token:
        """Expect a specific token type."""
        token = self._current()
        if token.type != token_type:
            raise SyntaxError(
                f"Expected {token_type.name}, got {token.type.name} at line {token.line}"
            )
        return self._advance()

    def _skip_newlines(self) -> None:
        """Skip any newline tokens."""
        while self._current().type == TokenType.NEWLINE:
            self._advance()

    def parse(self) -> tuple[TapeConfig, list]:
        """Parse .tg file into config and actions."""
        # Tokenize everything first
        self.tokens = list(self.tokenizer.tokenize())
        self.pos = 0

        config = TapeConfig()
        actions: list = []

        while self._current().type != TokenType.EOF:
            self._skip_newlines()

            if self._current().type == TokenType.EOF:
                break

            # Configuration directives
            if self._current().type == TokenType.AT_OUTPUT:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.output = token.value

            elif self._current().type == TokenType.AT_SIZE:
                self._advance()
                token = self._expect(TokenType.DIMENSIONS)
                w, h = token.value.split("x")
                config.width = int(w)
                config.height = int(h)

            elif self._current().type == TokenType.AT_FONT:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.font_size = int(token.value)

            elif self._current().type == TokenType.AT_SPEED:
                self._advance()
                token = self._expect(TokenType.DURATION)
                config.typing_speed_ms = parse_duration(token.value)

            elif self._current().type == TokenType.AT_LOOP:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.loop = int(token.value)

            elif self._current().type == TokenType.AT_TITLE:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.title = token.value

            elif self._current().type == TokenType.AT_QUALITY:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.quality = max(1, min(3, int(token.value)))  # Clamp 1-3

            elif self._current().type == TokenType.AT_BARE:
                self._advance()
                config.chrome = False  # Bare mode = no chrome

            elif self._current().type == TokenType.AT_FPS:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.fps = max(1, min(60, int(token.value)))  # Clamp 1-60

            elif self._current().type == TokenType.AT_THEME:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.theme = token.value.lower()

            elif self._current().type == TokenType.AT_PADDING:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.padding = int(token.value)

            elif self._current().type == TokenType.AT_PROMPT:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.prompt = token.value

            elif self._current().type == TokenType.AT_CURSOR:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.cursor = token.value.lower()

            elif self._current().type == TokenType.AT_START:
                self._advance()
                token = self._expect(TokenType.DURATION)
                config.start_delay = parse_duration(token.value)

            elif self._current().type == TokenType.AT_END:
                self._advance()
                token = self._expect(TokenType.DURATION)
                config.end_delay = parse_duration(token.value)

            elif self._current().type == TokenType.AT_RADIUS:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.radius = max(0, int(token.value))  # No negative radius

            elif self._current().type == TokenType.AT_RADIUS_OUTER:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.radius_outer = max(0, int(token.value))

            elif self._current().type == TokenType.AT_RADIUS_INNER:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.radius_inner = max(0, int(token.value))

            elif self._current().type == TokenType.AT_NATIVE:
                self._advance()
                config.native_colors = True

            # Actions
            elif self._current().type == TokenType.ARROW:
                self._advance()
                token = self._expect(TokenType.STRING)
                actions.append(TypeAction(text=token.value))

                # Check for >> after type
                if self._current().type == TokenType.DOUBLE_ARROW:
                    self._advance()
                    actions.append(EnterAction())

            elif self._current().type == TokenType.DOUBLE_ARROW:
                self._advance()
                actions.append(EnterAction())

            elif self._current().type == TokenType.DURATION:
                # Standalone ~duration (tilde was consumed by tokenizer)
                token = self._advance()
                actions.append(SleepAction(duration_ms=parse_duration(token.value)))

            elif self._current().type == TokenType.KEY:
                # key "escape" - special key press for TUI interaction
                self._advance()
                token = self._expect(TokenType.STRING)
                actions.append(KeyAction(key=token.value.lower()))

            else:
                raise SyntaxError(
                    f"Unexpected token {self._current().type.name} at line {self._current().line}"
                )

        return config, actions


def parse_tg(path: Path) -> tuple[TapeConfig, list]:
    """Parse a .tg file into config and actions."""
    content = path.read_text()
    parser = TgParser(content)
    return parser.parse()
