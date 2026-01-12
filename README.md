# termgif

[![PyPI version](https://img.shields.io/pypi/v/termgif)](https://pypi.org/project/termgif/)
[![Python](https://img.shields.io/pypi/pyversions/termgif)](https://pypi.org/project/termgif/)
[![License](https://img.shields.io/github/license/aayushadhikari7/termgif)](https://github.com/aayushadhikari7/termgif/blob/main/LICENSE)

Dead simple terminal GIF recorder. Write a script, get a beautiful GIF.

![termgif demo](https://raw.githubusercontent.com/aayushadhikari7/termgif/main/assets/demo.gif)

## Install

```bash
pip install termgif
```

## Quick Start

```bash
termgif create demo      # create demo.tg from template
termgif demo             # run commands, record to GIF
```

## Recording Modes

### Default Mode (Live Commands)

Runs real commands and captures the output:

```bash
termgif demo
```

![live mode](https://raw.githubusercontent.com/aayushadhikari7/termgif/main/assets/live-demo.gif)

### Simulated Mode

Fake output - commands aren't actually executed. Great for demos:

```bash
termgif demo --simulate
termgif demo -s
```

### Terminal Capture Mode

Screen captures your actual terminal window while running the script:

```bash
termgif demo --terminal
termgif demo -t
```

![terminal mode](https://raw.githubusercontent.com/aayushadhikari7/termgif/main/assets/terminal-demo.gif)

## Script Format (.tg)

```
// demo.tg
@output "demo.gif"
@size 80x24
@font 16
@title "My CLI Tool"
@theme "mocha"

-> "echo 'Hello, world!'" >>
~1s

-> "ls -la" >>
~2s
```

## Config Reference

### Output & Layout

| Directive | Description | Default |
|-----------|-------------|---------|
| `@output "path"` | Output GIF path | `output.gif` |
| `@size WxH` | Terminal size (chars) | `80x24` |
| `@font N` | Font size (px) | `14` |
| `@padding N` | Content padding (px) | `20` |

### Timing

| Directive | Description | Default |
|-----------|-------------|---------|
| `@speed Nms` | Typing speed per char | `50ms` |
| `@start Nms` | Delay before starting | `500ms` |
| `@end Nms` | Hold final frame | `2s` |
| `@fps N` | Frames per second | `10` |

### Appearance

| Directive | Description | Default |
|-----------|-------------|---------|
| `@title "text"` | Window title | `termgif` |
| `@theme "name"` | Color theme | `mocha` |
| `@cursor "style"` | block / bar / underline | `block` |
| `@prompt "$ "` | Custom prompt | auto |
| `@bare` | No window chrome | off |

### Corners

| Directive | Description | Default |
|-----------|-------------|---------|
| `@radius N` | Corner radius (both) | `10` |
| `@radius-outer N` | Outer GIF edge | @radius |
| `@radius-inner N` | Inner window | @radius |

### Advanced

| Directive | Description | Default |
|-----------|-------------|---------|
| `@loop N` | 0=infinite, N=times | `0` |
| `@quality N` | 1=fast, 2=smooth, 3=ultra | `2` |

## Script Syntax

| Syntax | Description |
|--------|-------------|
| `-> "text"` | Type text |
| `>>` | Press enter |
| `-> "text" >>` | Type + enter |
| `~500ms` | Wait (ms or s) |
| `// comment` | Single-line comment |
| `/* ... */` | Multi-line comment |

## Themes

| Theme | Description |
|-------|-------------|
| `mocha` | Catppuccin Mocha (default) |
| `latte` | Catppuccin Latte (light) |
| `frappe` | Catppuccin Frappe |
| `macchiato` | Catppuccin Macchiato |
| `dracula` | Dracula |
| `nord` | Nord |
| `tokyo` | Tokyo Night |
| `gruvbox` | Gruvbox |

## CLI Options

```
termgif <script.tg> [options]

Options:
  -o, --output <path>    Override output path
  -b, --bare             No window chrome
  -s, --simulate         Simulated mode (no real commands)
  -t, --terminal         Terminal capture mode
  -v, --version          Show version
  -h, --help             Show help
```

## Example

```
// showcase.tg
@output "showcase.gif"
@size 80x24
@font 16
@speed 60ms
@title "my-awesome-cli"
@theme "dracula"
@radius 12
@quality 3

-> "my-cli --help" >>
~2s

-> "my-cli init myproject" >>
~1.5s

-> "cd myproject && my-cli run" >>
~3s
```

```bash
termgif showcase
```

## Features

- **Beautiful output** - macOS-style window chrome, traffic lights, shadows
- **8 themes** - Catppuccin, Dracula, Nord, Tokyo Night, Gruvbox
- **3 modes** - Live commands, simulated, or screen capture
- **Rounded corners** - Independent inner/outer radius
- **Pure Python** - No FFmpeg or browser automation
- **Cross-platform** - Windows, macOS, Linux

## License

MIT
