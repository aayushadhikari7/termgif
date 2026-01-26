# termgif

[![PyPI version](https://img.shields.io/pypi/v/termgif)](https://pypi.org/project/termgif/)
[![Python](https://img.shields.io/pypi/pyversions/termgif)](https://pypi.org/project/termgif/)
[![License](https://img.shields.io/github/license/aayushadhikari7/termgif)](https://github.com/aayushadhikari7/termgif/blob/main/LICENSE)

Dead simple terminal GIF recorder. Write a script, get a beautiful GIF.

![termgif demo](https://raw.githubusercontent.com/aayushadhikari7/termgif/main/assets/demo.gif)

## Why termgif?

- **One command** - `termgif demo` and you're done
- **Beautiful output** - macOS-style window chrome, traffic lights, shadows
- **TUI support** - Record vim, htop, fzf, lazygit, and more
- **8 themes** - Catppuccin, Dracula, Nord, Tokyo Night, Gruvbox
- **3 modes** - Live commands, simulated, or screen capture
- **Cross-platform** - Windows, macOS, Linux

## Install

```bash
pip install termgif
```

For TUI app support on Windows:

```bash
pip install pywinpty
```

## Quick Start

```bash
# Create a script from template
termgif create demo

# Edit demo.tg with your commands, then record
termgif demo
```

That's it! Your GIF is ready.

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

### Native Colors Mode

Preserve TUI app's own colors instead of applying termgif's theme:

```bash
termgif demo --native
termgif demo -n
```

## Script Format (.tg)

When you run `termgif create demo`, you get a **fully documented template** with every option as a commented example - just uncomment what you need:

```
// ============================================================================
//  demo.tg - termgif recording script
// ============================================================================

// -- Output --
@output "demo.gif"

// -- Terminal Dimensions --
@size 80x24                       // Width x Height in characters
// @size 120x30                   // Wider terminal (uncomment to use)
@font 16                          // Font size in pixels
@padding 20                       // Padding around content

// -- Timing --
@speed 50ms                       // Typing speed per character
// @speed 30ms                    // Faster typing (uncomment to use)
@start 500ms                      // Delay before recording starts
@end 2s                           // Hold final frame duration
@fps 10                           // Frames per second

// -- Appearance --
@title "demo"                     // Window title
@theme "mocha"                    // Color theme
// @theme "dracula"               // Try different themes!
@cursor "block"                   // block, bar, underline
@radius 10                        // Corner radius (0 = sharp)

// -- Advanced (uncomment to use) --
// @prompt "$ "                   // Custom prompt
// @bare                          // No window chrome
// @native                        // Keep TUI app's colors
// @loop 1                        // Play once (0=infinite)
// @quality 3                     // Ultra quality

// ================================ SCRIPT ====================================

-> "echo Hello, World!" >>
~1s

-> "ls -la" >>
~2s

// More examples included in template (vim, htop, git, etc.)
```

The generated template includes **ready-to-use examples** for common scenarios: git workflows, Docker commands, TUI apps (vim, htop, fzf, lazygit), and more - just uncomment and customize!

## Configuration Reference

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
| `@native` | Preserve TUI app colors | off |

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

### Basic Actions

| Syntax | Description |
|--------|-------------|
| `-> "text"` | Type text character by character |
| `>>` | Press Enter |
| `-> "text" >>` | Type text and press Enter |
| `~500ms` | Wait for duration (ms, s, or bare number) |
| `~2s` | Wait for 2 seconds |

### Special Keys (for TUI apps)

| Syntax | Description |
|--------|-------------|
| `key "escape"` | Press a special key |
| `key "ctrl+c"` | Press a key combination |

**Supported keys:**
- Navigation: `up`, `down`, `left`, `right`, `home`, `end`, `pageup`, `pagedown`
- Editing: `backspace`, `delete`, `tab`, `space`
- Control: `escape`, `enter`, `return`
- Function: `f1`-`f12`
- Modifiers: `ctrl+<key>`, `alt+<key>`, `shift+<key>`

### Comments

```
// Single-line comment

/* Multi-line
   comment */
```

## Recording TUI Apps

termgif can record interactive TUI apps like `vim`, `htop`, `fzf`, `lazygit`, etc:

```
// vim-demo.tg
@output "vim-demo.gif"
@native                        // Preserve vim's colors

-> "vim hello.txt" >>
~1s

key "i"                        // Enter insert mode
-> "Hello from Vim!"
~500ms

key "escape"                   // Back to normal mode
-> ":wq" >>                    // Save and quit
~1s
```

Run with:

```bash
termgif vim-demo
```

Or use terminal capture mode for full fidelity:

```bash
termgif vim-demo --terminal
```

## Themes

| Theme | Description |
|-------|-------------|
| `mocha` | Catppuccin Mocha (default, dark) |
| `latte` | Catppuccin Latte (light) |
| `frappe` | Catppuccin Frappe (medium dark) |
| `macchiato` | Catppuccin Macchiato (medium dark) |
| `dracula` | Dracula (dark purple) |
| `nord` | Nord (arctic blue) |
| `tokyo` | Tokyo Night (dark blue) |
| `gruvbox` | Gruvbox (retro dark) |

## CLI Options

```
termgif <script.tg> [options]

Options:
  -o, --output <path>    Override output path
  -b, --bare             No window chrome
  -s, --simulate         Simulated mode (no real commands)
  -t, --terminal         Terminal capture mode
  -n, --native           Preserve TUI app's native colors
  -v, --version          Show version
  -h, --help             Show help
```

## Examples

### Simple Demo

```
// hello.tg
@output "hello.gif"
@theme "dracula"

-> "echo 'Hello, World!'" >>
~2s
```

### CLI Tool Showcase

```
// showcase.tg
@output "showcase.gif"
@size 80x24
@font 16
@speed 60ms
@title "my-awesome-cli"
@theme "tokyo"
@radius 12
@quality 3

-> "my-cli --help" >>
~2s

-> "my-cli init myproject" >>
~1.5s

-> "cd myproject && my-cli run" >>
~3s
```

### Interactive TUI Recording

```
// htop-demo.tg
@output "htop.gif"
@native                        // Keep htop's colors
@end 3s

-> "htop" >>
~2s

key "F6"                       // Sort menu
~1s

key "down"
key "down"
key "enter"                    // Select sort option
~2s

key "q"                        // Quit
```

## License

MIT
