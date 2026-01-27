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
    @radius 10              - Corner radius in pixels

    @format "mp4"           - Output format
    @bitrate "2M"           - Video bitrate
    @codec "h264"           - Video codec
    @crf 23                 - Quality factor
    @dither "floyd-steinberg" - GIF dithering
    @colors 256             - Color palette size
    @optimize true          - Optimize output
    @lossy 80               - WebP/video quality

    -> "text"               - Type text
    >>                      - Press enter
    ~500ms                  - Sleep
    -> "text" >>            - Type + enter (combined)
    key "escape"            - Press special key

    // comment              - Single-line comment
    /* comment */           - Multi-line comment
"""
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Iterator

from ..config import TapeConfig, parse_duration
from ..actions import TypeAction, EnterAction, SleepAction, KeyAction


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

    # New v0.3.0 directives
    AT_FORMAT = auto()
    AT_BITRATE = auto()
    AT_CODEC = auto()
    AT_CRF = auto()
    AT_DITHER = auto()
    AT_COLORS = auto()
    AT_OPTIMIZE = auto()
    AT_LOSSY = auto()
    AT_WATERMARK = auto()
    AT_WATERMARK_POSITION = auto()
    AT_WATERMARK_OPACITY = auto()
    AT_CAPTION = auto()
    AT_CAPTION_POSITION = auto()
    AT_SHELL = auto()
    AT_ENV = auto()
    AT_CWD = auto()
    AT_TIMEOUT = auto()

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
    BOOLEAN = auto()

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

    DIRECTIVES = {
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
        # New v0.3.0 directives
        "format": TokenType.AT_FORMAT,
        "bitrate": TokenType.AT_BITRATE,
        "codec": TokenType.AT_CODEC,
        "crf": TokenType.AT_CRF,
        "dither": TokenType.AT_DITHER,
        "colors": TokenType.AT_COLORS,
        "optimize": TokenType.AT_OPTIMIZE,
        "lossy": TokenType.AT_LOSSY,
        "watermark": TokenType.AT_WATERMARK,
        "watermark-position": TokenType.AT_WATERMARK_POSITION,
        "watermark-opacity": TokenType.AT_WATERMARK_OPACITY,
        "caption": TokenType.AT_CAPTION,
        "caption-position": TokenType.AT_CAPTION_POSITION,
        "shell": TokenType.AT_SHELL,
        "env": TokenType.AT_ENV,
        "cwd": TokenType.AT_CWD,
        "timeout": TokenType.AT_TIMEOUT,
    }

    def __init__(self, content: str):
        self.content = content
        self.pos = 0
        self.line = 1
        self.column = 1

    def _current(self) -> str:
        if self.pos >= len(self.content):
            return ""
        return self.content[self.pos]

    def _peek(self, offset: int = 1) -> str:
        pos = self.pos + offset
        if pos >= len(self.content):
            return ""
        return self.content[pos]

    def _advance(self) -> str:
        char = self._current()
        self.pos += 1
        self.column += 1
        return char

    def _make_token(self, token_type: TokenType, value: str) -> Token:
        return Token(token_type, value, self.line, self.column)

    def _skip_line_comment(self) -> None:
        while self._current() and self._current() != "\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        self._advance()  # skip /
        self._advance()  # skip *
        while self._current():
            if self._current() == "*" and self._peek() == "/":
                self._advance()
                self._advance()
                return
            if self._current() == "\n":
                self.line += 1
                self.column = 0
            self._advance()
        raise SyntaxError(f"Unterminated block comment at line {self.line}")

    def _read_string(self) -> Token:
        start_line = self.line
        start_col = self.column
        self._advance()

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

        self._advance()
        return Token(TokenType.STRING, "".join(chars), start_line, start_col)

    def _read_directive(self) -> Token:
        start_col = self.column
        self._advance()  # skip @

        word = []
        while self._current() and (self._current().isalpha() or self._current() == "-"):
            word.append(self._advance())

        directive = "".join(word).lower()

        if directive not in self.DIRECTIVES:
            raise SyntaxError(f"Unknown directive @{directive} at line {self.line}")

        return Token(self.DIRECTIVES[directive], directive, self.line, start_col)

    def _read_duration(self) -> Token:
        start_col = self.column
        chars = []

        while self._current() and (self._current().isdigit() or self._current() == "."):
            chars.append(self._advance())

        while self._current() and self._current().isalpha():
            chars.append(self._advance())

        return Token(TokenType.DURATION, "".join(chars), self.line, start_col)

    def _read_number_or_dimensions(self) -> Token:
        start_col = self.column
        chars = []

        while self._current() and self._current().isdigit():
            chars.append(self._advance())

        if self._current() == "x" and self._peek().isdigit():
            chars.append(self._advance())
            while self._current() and self._current().isdigit():
                chars.append(self._advance())
            return Token(TokenType.DIMENSIONS, "".join(chars), self.line, start_col)

        if self._current() in ("m", "s"):
            while self._current() and self._current().isalpha():
                chars.append(self._advance())
            return Token(TokenType.DURATION, "".join(chars), self.line, start_col)

        return Token(TokenType.NUMBER, "".join(chars), self.line, start_col)

    def tokenize(self) -> Iterator[Token]:
        while self.pos < len(self.content):
            if self._current() in " \t\r":
                self._advance()
                continue

            if self._current() == "\n":
                yield self._make_token(TokenType.NEWLINE, "\n")
                self._advance()
                self.line += 1
                self.column = 1
                continue

            if self._current() == "/" and self._peek() == "/":
                self._skip_line_comment()
                continue
            if self._current() == "/" and self._peek() == "*":
                self._skip_block_comment()
                continue

            if self._current() == "@":
                yield self._read_directive()
                continue

            if self._current() == "-" and self._peek() == ">":
                yield self._make_token(TokenType.ARROW, "->")
                self._advance()
                self._advance()
                continue

            if self._current() == ">" and self._peek() == ">":
                yield self._make_token(TokenType.DOUBLE_ARROW, ">>")
                self._advance()
                self._advance()
                continue

            if self._current() == "~":
                self._advance()
                yield self._read_duration()
                continue

            if self._current() == '"':
                yield self._read_string()
                continue

            if self._current().isdigit():
                yield self._read_number_or_dimensions()
                continue

            if self._current().isalpha():
                start_col = self.column
                word = []
                while self._current() and self._current().isalnum():
                    word.append(self._advance())
                keyword = "".join(word).lower()

                if keyword == "key":
                    yield Token(TokenType.KEY, "key", self.line, start_col)
                    continue
                elif keyword in ("true", "false"):
                    yield Token(TokenType.BOOLEAN, keyword, self.line, start_col)
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
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        token = self._current()
        self.pos += 1
        return token

    def _expect(self, token_type: TokenType) -> Token:
        token = self._current()
        if token.type != token_type:
            raise SyntaxError(
                f"Expected {token_type.name}, got {token.type.name} at line {token.line}"
            )
        return self._advance()

    def _skip_newlines(self) -> None:
        while self._current().type == TokenType.NEWLINE:
            self._advance()

    def parse(self) -> tuple[TapeConfig, list]:
        self.tokens = list(self.tokenizer.tokenize())
        self.pos = 0

        config = TapeConfig()
        actions: list = []

        while self._current().type != TokenType.EOF:
            self._skip_newlines()

            if self._current().type == TokenType.EOF:
                break

            # Configuration directives
            token_type = self._current().type

            if token_type == TokenType.AT_OUTPUT:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.output = token.value

            elif token_type == TokenType.AT_SIZE:
                self._advance()
                token = self._expect(TokenType.DIMENSIONS)
                w, h = token.value.split("x")
                config.width = int(w)
                config.height = int(h)

            elif token_type == TokenType.AT_FONT:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.font_size = int(token.value)

            elif token_type == TokenType.AT_SPEED:
                self._advance()
                token = self._expect(TokenType.DURATION)
                config.typing_speed_ms = parse_duration(token.value)

            elif token_type == TokenType.AT_LOOP:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.loop = int(token.value)

            elif token_type == TokenType.AT_TITLE:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.title = token.value

            elif token_type == TokenType.AT_QUALITY:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.quality = max(1, min(3, int(token.value)))

            elif token_type == TokenType.AT_BARE:
                self._advance()
                config.chrome = False

            elif token_type == TokenType.AT_FPS:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.fps = max(1, min(60, int(token.value)))

            elif token_type == TokenType.AT_THEME:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.theme = token.value.lower()

            elif token_type == TokenType.AT_PADDING:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.padding = int(token.value)

            elif token_type == TokenType.AT_PROMPT:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.prompt = token.value

            elif token_type == TokenType.AT_CURSOR:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.cursor = token.value.lower()

            elif token_type == TokenType.AT_START:
                self._advance()
                token = self._expect(TokenType.DURATION)
                config.start_delay = parse_duration(token.value)

            elif token_type == TokenType.AT_END:
                self._advance()
                token = self._expect(TokenType.DURATION)
                config.end_delay = parse_duration(token.value)

            elif token_type == TokenType.AT_RADIUS:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.radius = max(0, int(token.value))

            elif token_type == TokenType.AT_RADIUS_OUTER:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.radius_outer = max(0, int(token.value))

            elif token_type == TokenType.AT_RADIUS_INNER:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.radius_inner = max(0, int(token.value))

            elif token_type == TokenType.AT_NATIVE:
                self._advance()
                config.native_colors = True

            # New v0.3.0 directives
            elif token_type == TokenType.AT_FORMAT:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.format = token.value.lower()

            elif token_type == TokenType.AT_BITRATE:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.bitrate = token.value

            elif token_type == TokenType.AT_CODEC:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.codec = token.value.lower()

            elif token_type == TokenType.AT_CRF:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.crf = int(token.value)

            elif token_type == TokenType.AT_DITHER:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.dither = token.value

            elif token_type == TokenType.AT_COLORS:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.colors = int(token.value)

            elif token_type == TokenType.AT_OPTIMIZE:
                self._advance()
                if self._current().type == TokenType.BOOLEAN:
                    config.optimize = self._advance().value == "true"
                else:
                    config.optimize = True

            elif token_type == TokenType.AT_LOSSY:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.lossy = int(token.value)

            elif token_type == TokenType.AT_WATERMARK:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.watermark = token.value

            elif token_type == TokenType.AT_WATERMARK_POSITION:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.watermark_position = token.value

            elif token_type == TokenType.AT_WATERMARK_OPACITY:
                self._advance()
                token = self._expect(TokenType.NUMBER)
                config.watermark_opacity = float(token.value)

            elif token_type == TokenType.AT_CAPTION:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.caption = token.value

            elif token_type == TokenType.AT_CAPTION_POSITION:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.caption_position = token.value

            elif token_type == TokenType.AT_SHELL:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.shell = token.value

            elif token_type == TokenType.AT_ENV:
                self._advance()
                token = self._expect(TokenType.STRING)
                if config.env is None:
                    config.env = []
                config.env.append(token.value)

            elif token_type == TokenType.AT_CWD:
                self._advance()
                token = self._expect(TokenType.STRING)
                config.cwd = token.value

            elif token_type == TokenType.AT_TIMEOUT:
                self._advance()
                token = self._expect(TokenType.DURATION)
                config.timeout = parse_duration(token.value)

            # Actions
            elif token_type == TokenType.ARROW:
                self._advance()
                token = self._expect(TokenType.STRING)
                actions.append(TypeAction(text=token.value))

                if self._current().type == TokenType.DOUBLE_ARROW:
                    self._advance()
                    actions.append(EnterAction())

            elif token_type == TokenType.DOUBLE_ARROW:
                self._advance()
                actions.append(EnterAction())

            elif token_type == TokenType.DURATION:
                token = self._advance()
                actions.append(SleepAction(ms=parse_duration(token.value)))

            elif token_type == TokenType.KEY:
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
