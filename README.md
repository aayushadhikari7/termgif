# termgif

[![PyPI version](https://img.shields.io/pypi/v/termgif)](https://pypi.org/project/termgif/)
[![Python](https://img.shields.io/pypi/pyversions/termgif)](https://pypi.org/project/termgif/)
[![License](https://img.shields.io/github/license/aayushadhikari7/termgif)](https://github.com/aayushadhikari7/termgif/blob/main/LICENSE)

Terminal recording studio. Create beautiful terminal recordings as GIF, MP4, WebP, and more.

![termgif demo](https://raw.githubusercontent.com/aayushadhikari7/termgif/main/assets/demo.gif)

## Features

- **Multiple formats** - GIF, WebP, MP4, WebM, APNG, SVG, PNG frames, Asciinema
- **Live recording** - Record your actual terminal session without scripts
- **Watch mode** - Auto-regenerate recordings when script files change
- **Built-in templates** - git, npm, docker, python, vim, htop, lazygit, and more
- **Editing tools** - Trim, speed adjustment, concatenation, watermarks, captions
- **Asciinema compatible** - Import/export .cast files
- **Direct sharing** - Upload to Catbox, Imgur, or Giphy
- **TUI support** - Record vim, htop, fzf, lazygit, and other TUI applications
- **8 themes** - Catppuccin (mocha, latte, frappe, macchiato), Dracula, Nord, Tokyo Night, Gruvbox
- **Cross-platform** - Windows, macOS, Linux

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Recording Modes](#recording-modes)
- [Script Format (.tg)](#script-format-tg)
- [Output Formats](#output-formats)
- [Templates](#templates)
- [Live Recording](#live-recording)
- [Watch Mode](#watch-mode)
- [Editing Tools](#editing-tools)
- [Asciinema Import/Export](#asciinema-importexport)
- [Sharing & Upload](#sharing--upload)
- [Configuration](#configuration)
- [Themes](#themes)
- [CLI Reference](#cli-reference)
- [Troubleshooting](#troubleshooting)

---

## Installation

```bash
# Basic installation
pip install termgif

# With video format support (MP4, WebM - requires ffmpeg)
pip install termgif[video]

# With sharing support (upload to Catbox, Imgur, Giphy)
pip install termgif[share]

# With watch mode support
pip install termgif[watch]

# Everything
pip install termgif[all]
```

### System Requirements

- **Python 3.10+**
- **ffmpeg** (optional) - Required for MP4/WebM output. Install via:
  - Windows: `winget install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/)
  - macOS: `brew install ffmpeg`
  - Linux: `apt install ffmpeg` or equivalent

---

## Quick Start

### 1. Create a script from template

```bash
termgif create demo --template git
```

This creates `demo.tg` with a git workflow template.

### 2. Record to GIF

```bash
termgif demo
```

This runs the commands in `demo.tg` and creates `demo.gif`.

### 3. Use different formats

```bash
termgif demo -f mp4      # MP4 video
termgif demo -f webp     # WebP animation
termgif demo -o out.webm # Auto-detect from extension
```

### 4. Watch mode for rapid iteration

```bash
termgif demo --watch
```

The GIF auto-regenerates whenever you save changes to `demo.tg`.

---

## Recording Modes

termgif has three recording modes:

### Live Mode (default)

```bash
termgif demo.tg
```

- **Executes real commands** and captures actual output
- Best for authentic recordings
- Commands run in your actual shell

### Simulate Mode

```bash
termgif demo.tg --simulate
```

- **Does NOT execute any commands** - completely safe
- Only shows typing animation, no command output
- Use this when you want to show the typing without running anything
- Perfect for demos where actual output isn't needed

### Terminal Mode (Screen Capture)

```bash
termgif demo.tg --terminal
```

- Captures the actual terminal window
- Required for TUI apps (vim, htop, lazygit, etc.)
- Preserves exact terminal appearance
- Use `--native` to preserve TUI app colors

```bash
termgif demo.tg --terminal --native
```

---

## Script Format (.tg)

Scripts use the `.tg` format with directives and actions.

### Basic Example

```
// demo.tg - My first recording
// Comments start with //

@output "demo.gif"
@size 80x24
@theme "mocha"
@fps 10
@speed 50ms

// Type and execute commands
-> "echo Hello, World!" >>
~1s

-> "ls -la" >>
~2s

// Just type without pressing enter
-> "partial command"
~500ms
```

### Directives

Directives configure the recording. They start with `@`.

| Directive | Example | Description |
|-----------|---------|-------------|
| `@output` | `@output "demo.gif"` | Output file path |
| `@size` | `@size 80x24` | Terminal size (columns x rows) |
| `@font` | `@font 16` | Font size in pixels |
| `@theme` | `@theme "dracula"` | Color theme |
| `@fps` | `@fps 12` | Frames per second |
| `@speed` | `@speed 50ms` | Typing speed per character |
| `@format` | `@format "mp4"` | Output format override |
| `@title` | `@title "My Demo"` | Window title |
| `@prompt` | `@prompt "$ "` | Full custom prompt |
| `@user` | `@user "demo"` | Username in prompt |
| `@hostname` | `@hostname "server"` | Hostname in prompt |
| `@symbol` | `@symbol "#"` | Prompt symbol ($ or #) |
| `@cursor` | `@cursor "bar"` | Cursor style: block, bar, underline |
| `@cursor-color` | `@cursor-color "#cba6f7"` | Custom cursor color |
| `@shell` | `@shell "zsh"` | Shell to use |
| `@bare` | `@bare` | No window chrome (border/title) |
| `@native` | `@native` | Preserve TUI app colors |
| `@chrome` | `@chrome false` | Disable window chrome |
| `@shadow` | `@shadow false` | Disable window shadow |
| `@glow` | `@glow false` | Disable glow effect |
| `@window-frame` | `@window-frame "minimal"` | Frame style: macos, windows, minimal, none |
| `@line-height` | `@line-height 1.5` | Line height multiplier |
| `@letter-spacing` | `@letter-spacing 1` | Extra character spacing |
| `@start_delay` | `@start_delay 500ms` | Delay before first action |
| `@end_delay` | `@end_delay 2s` | Delay after last action |

### Actions

Actions define what happens in the recording.

| Syntax | Description | Example |
|--------|-------------|---------|
| `-> "text"` | Type text | `-> "echo hello"` |
| `>>` | Press Enter | `>>` |
| `-> "text" >>` | Type and press Enter | `-> "git status" >>` |
| `~duration` | Wait/pause | `~1s`, `~500ms`, `~2000ms` |
| `key "name"` | Press special key | `key "escape"` |
| `hide` | Pause frame capture | `hide` |
| `show` | Resume frame capture | `show` |
| `screenshot "file.png"` | Save current frame | `screenshot "step1.png"` |
| `marker "name"` | Add chapter marker | `marker "Setup"` |
| `require "cmd"` | Check command exists | `require "docker"` |

### Duration Format

Durations can be specified as:
- `~1s` - 1 second
- `~500ms` - 500 milliseconds
- `~2000ms` - 2000 milliseconds (2 seconds)

### Special Keys

For TUI apps (requires `--terminal` mode):

| Key | Description |
|-----|-------------|
| `key "escape"` | Escape key |
| `key "enter"` | Enter key |
| `key "tab"` | Tab key |
| `key "backspace"` | Backspace |
| `key "up"` | Arrow up |
| `key "down"` | Arrow down |
| `key "left"` | Arrow left |
| `key "right"` | Arrow right |
| `key "ctrl+c"` | Ctrl+C |
| `key "ctrl+d"` | Ctrl+D |
| `key "ctrl+z"` | Ctrl+Z |
| `key "space"` | Space |
| `key "home"` | Home |
| `key "end"` | End |
| `key "pageup"` | Page Up |
| `key "pagedown"` | Page Down |
| `key "f1"` - `key "f12"` | Function keys |

### Complete Example

```
// vim-demo.tg - Demonstrate vim editing
@output "vim-demo.gif"
@title "Vim Tutorial"
@theme "tokyo"
@size 100x30
@fps 12

// Open vim
-> "vim example.py" >>
~1s

// Enter insert mode
key "i"
~200ms

// Type some code
-> "def hello():"
key "enter"
-> "    print('Hello!')"
~500ms

// Exit insert mode
key "escape"
~200ms

// Save and quit
-> ":wq" >>
~1s
```

---

## Output Formats

termgif supports multiple output formats:

| Format | Extension | Description | Requirements |
|--------|-----------|-------------|--------------|
| GIF | `.gif` | Animated GIF (default) | None |
| WebP | `.webp` | Smaller than GIF, good quality | None |
| MP4 | `.mp4` | Video format, smallest size | ffmpeg |
| WebM | `.webm` | Open video format | ffmpeg |
| APNG | `.apng` | Animated PNG, full colors | None |
| SVG | `.svg` | Scalable vector graphics | None |
| Frames | folder | PNG sequence for editing | None |
| Cast | `.cast` | Asciinema format | None |

### Usage

```bash
# Specify format with -f flag
termgif demo -f mp4
termgif demo -f webp
termgif demo -f apng

# Or use output extension (auto-detect)
termgif demo -o output.mp4
termgif demo -o output.webp

# Export as PNG frames
termgif demo -f frames -o ./frames/

# Export as asciinema cast
termgif demo -f cast -o demo.cast
```

### Format Comparison

| Format | Size | Quality | Browser Support | Best For |
|--------|------|---------|-----------------|----------|
| GIF | Large | Limited colors | Universal | Quick sharing |
| WebP | Small | Good | Modern browsers | Web use |
| MP4 | Smallest | Excellent | Universal | Long recordings |
| WebM | Small | Excellent | Modern browsers | Open source projects |
| APNG | Medium | Full colors | Most browsers | High quality stills |

---

## Templates

Templates provide ready-to-use scripts for common workflows.

### List Available Templates

```bash
termgif templates
```

### Create from Template

```bash
termgif create myproject --template git
```

### Available Templates

| Template | Description |
|----------|-------------|
| `basic` | Simple echo commands |
| `git` | Git workflow (status, add, commit, push) |
| `npm` | npm install and run |
| `docker` | Docker build and run |
| `python` | Python REPL session |
| `pip` | pip install packages |
| `vim` | Vim editing session |
| `htop` | System monitoring with htop |
| `lazygit` | Git TUI with lazygit |
| `api` | API calls with curl |

### Template Variables

Templates use `{name}` placeholders that get replaced:

```bash
termgif create myapp --template git
# Creates myapp.tg with "myapp" in output filename
```

---

## Live Recording

Record your actual terminal session without a script:

```bash
# Basic live recording
termgif live -o session.gif

# With custom size
termgif live -o session.gif --size 100x30

# With specific duration limit
termgif live -o session.gif --duration 60s

# As MP4
termgif live -o session.mp4
```

**Controls during live recording:**
- `Ctrl+C` - Stop recording and save
- Your terminal session is captured in real-time

---

## Watch Mode

Auto-regenerate recordings when script files change:

```bash
termgif demo.tg --watch
# or
termgif demo.tg -w
```

This is useful for rapid iteration:
1. Edit your `.tg` script
2. Save the file
3. Recording automatically regenerates

Press `Ctrl+C` to exit watch mode.

---

## Editing Tools

### Trim

Remove frames from the start or end:

```bash
# Remove first 2 seconds
termgif trim demo.gif -s 2s -o trimmed.gif

# Remove last 1 second
termgif trim demo.gif -e -1s -o trimmed.gif

# Both
termgif trim demo.gif -s 2s -e -1s -o trimmed.gif

# By frame number
termgif trim demo.gif --start-frame 10 --end-frame 50 -o trimmed.gif
```

### Speed

Change playback speed:

```bash
# 2x faster
termgif speed demo.gif 2x -o fast.gif

# Half speed
termgif speed demo.gif 0.5x -o slow.gif

# 3x faster
termgif speed demo.gif 3x -o triple.gif
```

### Concatenate

Join multiple recordings:

```bash
termgif concat intro.gif main.gif outro.gif -o full.gif
```

### Overlay

Add watermarks or captions:

```bash
# Add watermark image
termgif overlay demo.gif --watermark logo.png -o branded.gif

# Position watermark (tl, tr, bl, br for corners)
termgif overlay demo.gif --watermark logo.png --position br -o branded.gif

# Set watermark opacity (0.0 to 1.0)
termgif overlay demo.gif --watermark logo.png --opacity 0.3 -o branded.gif

# Add text caption
termgif overlay demo.gif --text "My Demo" --position bottom -o captioned.gif
```

---

## Asciinema Import/Export

### Import .cast to GIF/Video

Convert asciinema recordings to other formats:

```bash
# To GIF
termgif import session.cast -o demo.gif

# To MP4
termgif import session.cast -f mp4 -o demo.mp4

# To WebP
termgif import session.cast -f webp -o demo.webp

# With custom theme
termgif import session.cast -o demo.gif --theme dracula
```

### Export Script to .cast

Export your `.tg` script as asciinema format:

```bash
termgif export demo.tg -o session.cast
```

This creates a `.cast` file that can be played with `asciinema play`.

---

## Sharing & Upload

Upload recordings directly to hosting services.

### Catbox (Default)

Anonymous upload, no account required:

```bash
termgif upload demo.gif
# Returns: https://files.catbox.moe/abc123.gif
```

Files are hosted temporarily (check Catbox's retention policy).

### Imgur

Requires API client ID:

```bash
termgif upload demo.gif imgur
```

Setup:
1. Create an Imgur account
2. Register an application at https://api.imgur.com/oauth2/addclient
3. Add client ID to config (see Configuration section)

### Giphy

Requires API key (GIF files only):

```bash
termgif upload demo.gif giphy
```

Setup:
1. Create a Giphy developer account
2. Create an app at https://developers.giphy.com/
3. Add API key to config

---

## Configuration

### Create Config File

```bash
termgif config --init
```

This creates the config file at:
- **Linux/macOS:** `~/.config/termgif/config.toml`
- **Windows:** `%APPDATA%\termgif\config.toml`

### Edit Config

```bash
termgif config --edit
```

Opens the config file in your default editor.

### View Current Config

```bash
termgif config
```

### Config File Structure

```toml
# ~/.config/termgif/config.toml

[defaults]
theme = "mocha"
font_size = 16
fps = 10
format = "gif"
width = 80
height = 24

[sharing]
# Get from https://api.imgur.com/oauth2/addclient
imgur_client_id = "your_imgur_client_id"

# Get from https://developers.giphy.com/
giphy_api_key = "your_giphy_api_key"

[paths]
# Custom templates directory
templates = "~/.config/termgif/templates"

[editor]
# Preferred editor for config --edit
command = "code"  # or "vim", "nano", etc.
```

---

## Themes

termgif includes 8 color themes:

| Theme | Description |
|-------|-------------|
| `mocha` | Catppuccin Mocha (warm dark) - **default** |
| `latte` | Catppuccin Latte (light) |
| `frappe` | Catppuccin Frappé (cool dark) |
| `macchiato` | Catppuccin Macchiato (medium dark) |
| `dracula` | Dracula (purple dark) |
| `nord` | Nord (blue-gray dark) |
| `tokyo` | Tokyo Night (blue dark) |
| `gruvbox` | Gruvbox (retro dark) |

### Usage in Scripts

```
@theme "dracula"
```

### Usage via CLI

```bash
termgif demo.tg --theme tokyo
```

---

## CLI Reference

### Main Commands

```
termgif <script>                    Record a .tg script
termgif record <script>             Same as above
termgif create <name>               Create new script from template
termgif live                        Live recording mode
termgif templates                   List available templates
termgif preview <file>              Preview a recording
termgif info <file>                 Show file information
```

### Editing Commands

```
termgif trim <file>                 Trim start/end of recording
termgif speed <file> <multiplier>   Change playback speed
termgif concat <files...> -o out    Concatenate recordings
termgif overlay <file>              Add watermark or caption
```

### Import/Export Commands

```
termgif import <file.cast>          Import asciinema recording
termgif export <script.tg>          Export script to asciinema format
```

### Sharing Commands

```
termgif upload <file>               Upload to Catbox (default)
termgif upload <file> imgur         Upload to Imgur
termgif upload <file> giphy         Upload to Giphy
```

### Configuration Commands

```
termgif config                      Show current configuration
termgif config --init               Create default config file
termgif config --edit               Edit config in default editor
```

### Recording Options

| Flag | Short | Description |
|------|-------|-------------|
| `--output` | `-o` | Output file path |
| `--format` | `-f` | Output format (gif, mp4, webp, etc.) |
| `--bare` | `-b` | No window chrome (border/title bar) |
| `--simulate` | `-s` | Don't execute commands (safe mode) |
| `--terminal` | `-t` | Screen capture mode for TUI apps |
| `--native` | `-n` | Preserve TUI app colors |
| `--watch` | `-w` | Auto-regenerate on file changes |
| `--theme` | | Override color theme |
| `--size` | | Override terminal size (WxH) |

### Examples

```bash
# Create and record a git demo
termgif create mygit --template git
termgif mygit

# Record with different format
termgif demo -f mp4 -o demo.mp4

# Safe recording (no commands executed)
termgif demo --simulate

# Record vim session
termgif vim-demo --terminal --native

# Quick iteration with watch mode
termgif demo --watch

# Edit and share
termgif trim demo.gif -s 1s -o trimmed.gif
termgif upload trimmed.gif
```

---

## Troubleshooting

### "ffmpeg not found" for MP4/WebM

Install ffmpeg:
- Windows: `winget install ffmpeg`
- macOS: `brew install ffmpeg`
- Linux: `apt install ffmpeg`

### "requests not installed" for upload

```bash
pip install termgif[share]
# or
pip install requests
```

### TUI apps not rendering correctly

Use terminal mode with native colors:

```bash
termgif demo --terminal --native
```

### Commands not executing

Check you're not using `--simulate` flag. In simulate mode, commands are displayed but not executed.

### GIF too large

Try these options:
1. Use WebP format: `termgif demo -f webp`
2. Use MP4 format: `termgif demo -f mp4`
3. Reduce FPS in script: `@fps 8`
4. Reduce terminal size: `@size 60x20`

### Watch mode not detecting changes

Install watchdog:

```bash
pip install termgif[watch]
# or
pip install watchdog
```

### Colors look wrong

1. Try a different theme: `@theme "dracula"`
2. For TUI apps, use `--native` flag
3. Check your terminal supports 256 colors

---

## License

MIT

---

## Contributing

Contributions are welcome! Please open an issue or pull request on [GitHub](https://github.com/aayushadhikari7/termgif).
