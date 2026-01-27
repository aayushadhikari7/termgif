# termgif

[![PyPI version](https://img.shields.io/pypi/v/termgif)](https://pypi.org/project/termgif/)
[![Python](https://img.shields.io/pypi/pyversions/termgif)](https://pypi.org/project/termgif/)
[![License](https://img.shields.io/github/license/aayushadhikari7/termgif)](https://github.com/aayushadhikari7/termgif/blob/main/LICENSE)

Terminal recording studio. GIF, MP4, WebP, and more.

![termgif demo](https://raw.githubusercontent.com/aayushadhikari7/termgif/main/assets/demo.gif)

## Features

- **Multiple formats** - GIF, WebP, MP4, WebM, APNG, SVG, PNG frames
- **Live recording** - Record without scripts using `termgif live`
- **Watch mode** - Auto-regenerate on file changes
- **Built-in templates** - git, npm, docker, python, vim, htop, and more
- **Editing tools** - Trim, speed, concat, watermark, caption
- **Asciinema compatible** - Import/export .cast files
- **Direct sharing** - Upload to Catbox, Imgur, or Giphy
- **TUI support** - Record vim, htop, fzf, lazygit
- **8 themes** - Catppuccin, Dracula, Nord, Tokyo Night, Gruvbox
- **Cross-platform** - Windows, macOS, Linux

## Install

```bash
pip install termgif

# Optional: video formats (MP4, WebM)
pip install termgif[video]

# Optional: sharing support
pip install termgif[share]

# Everything
pip install termgif[all]
```

## Quick Start

```bash
# Create from template
termgif create demo --template git

# Record to GIF
termgif demo

# Record to MP4
termgif demo -f mp4

# Watch mode (auto-regenerate)
termgif demo --watch
```

## Live Recording

Record your terminal without a script:

```bash
termgif live -o session.gif
```

Press `Ctrl+C` to stop recording.

## Output Formats

```bash
termgif demo                    # GIF (default)
termgif demo -f webp            # WebP (smaller)
termgif demo -f mp4             # MP4 (requires ffmpeg)
termgif demo -f webm            # WebM (requires ffmpeg)
termgif demo -f apng            # Animated PNG
termgif demo -f svg             # SVG
termgif demo -f frames          # PNG sequence
```

## Templates

```bash
termgif templates               # List available templates

termgif create demo --template basic
termgif create demo --template git
termgif create demo --template npm
termgif create demo --template docker
termgif create demo --template python
termgif create demo --template vim
termgif create demo --template htop
termgif create demo --template lazygit
termgif create demo --template api
```

## Editing

```bash
# Trim start/end
termgif trim demo.gif -s 2s -e -1s -o trimmed.gif

# Change speed
termgif speed demo.gif 2x -o fast.gif

# Concatenate
termgif concat part1.gif part2.gif -o full.gif

# Add watermark
termgif overlay demo.gif --watermark logo.png -o branded.gif

# Add caption
termgif overlay demo.gif --text "Demo" --position bottom -o captioned.gif
```

## Asciinema Import/Export

```bash
# Import .cast to GIF
termgif import session.cast -o demo.gif

# Import .cast to MP4
termgif import session.cast -f mp4 -o demo.mp4

# Export script to .cast
termgif export demo.tg -o session.cast
```

## Sharing

```bash
# Upload to Catbox (anonymous, no account needed)
termgif upload demo.gif

# Upload to Imgur (requires API key in config)
termgif upload demo.gif imgur

# Upload to Giphy (requires API key in config)
termgif upload demo.gif giphy
```

## Configuration

```bash
termgif config --init           # Create default config
termgif config --edit           # Edit config in editor
termgif config                  # Show current config
```

Config file location:
- Linux/macOS: `~/.config/termgif/config.toml`
- Windows: `%APPDATA%\termgif\config.toml`

## Recording Modes

```bash
termgif demo                    # Live (runs real commands)
termgif demo --simulate         # Simulated (fake output)
termgif demo --terminal         # Screen capture
termgif demo --native           # Preserve TUI colors
```

## Script Format (.tg)

```
@output "demo.gif"
@size 80x24
@theme "mocha"
@fps 10

-> "echo Hello" >>
~1s
-> "ls -la" >>
~2s
```

### Directives

| Directive | Description |
|-----------|-------------|
| `@output "path"` | Output path |
| `@size WxH` | Terminal size |
| `@font N` | Font size (px) |
| `@theme "name"` | Color theme |
| `@fps N` | Frames per second |
| `@speed Nms` | Typing speed |
| `@format "fmt"` | Output format |
| `@bare` | No window chrome |
| `@native` | Keep TUI colors |

### Actions

| Syntax | Description |
|--------|-------------|
| `-> "text"` | Type text |
| `>>` | Press Enter |
| `-> "text" >>` | Type and Enter |
| `~1s` | Wait |
| `key "escape"` | Press key |

## Themes

`mocha`, `latte`, `frappe`, `macchiato`, `dracula`, `nord`, `tokyo`, `gruvbox`

## CLI Reference

```
termgif <script>                Record a script
termgif create <name>           Create new script
termgif live                    Live recording mode
termgif templates               List templates
termgif preview <file>          Preview recording
termgif info <file>             Show file info
termgif trim <file>             Trim recording
termgif speed <file> <2x>       Change speed
termgif concat <files> -o out   Concatenate
termgif overlay <file>          Add overlay
termgif import <file.cast>      Import asciinema
termgif export <script>         Export to asciinema
termgif upload <file>           Upload to sharing service
termgif config                  Configuration
```

## License

MIT
