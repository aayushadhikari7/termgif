"""CLI for termgif."""
import sys
import webbrowser
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel

from . import __version__
from .recorder import record_script
from .capture import record_live, record_terminal, HAS_CAPTURE

console = Console()
GITHUB_URL = "https://github.com/aayushadhikari7/termgif"


def _check_first_run():
    """Check if this is the first run and show welcome message."""
    marker = Path.home() / ".termgif_welcomed"
    if not marker.exists():
        console.print(Panel(
            f"[bold cyan]Welcome to termgif![/]\n\n"
            f"Dead simple terminal GIF recorder.\n\n"
            f"[dim]Like it? Give us a star:[/] [link={GITHUB_URL}]{GITHUB_URL}[/link]",
            title="termgif",
            border_style="cyan"
        ))
        try:
            webbrowser.open(GITHUB_URL)
        except Exception:
            pass  # Silently fail if browser can't open
        marker.touch()
        console.print()

BOILERPLATE = '''// ============================================================================
//  {name}.tg - termgif recording script
// ============================================================================
//
//  QUICK START:
//    termgif {name}              Run commands & record to GIF
//    termgif {name} --simulate   Preview without running commands
//    termgif {name} --terminal   Screen-capture your actual terminal
//
//  DOCUMENTATION: https://github.com/aayushadhikari7/termgif
//
// ============================================================================


// ============================= CONFIGURATION ================================
//
// All settings have sensible defaults. Uncomment and modify as needed!
//

// -- Output --
@output "{name}.gif"              // Output file path


// -- Terminal Dimensions --
@size 80x24                       // Width x Height in characters
// @size 120x30                   // Wider terminal for more content
// @size 60x20                    // Compact size

@font 16                          // Font size in pixels (affects GIF size)
// @font 14                       // Smaller text, smaller GIF
// @font 20                       // Larger text, larger GIF

@padding 20                       // Padding around terminal content (px)
// @padding 0                     // No padding (edge-to-edge)
// @padding 40                    // Extra breathing room


// -- Timing --
@speed 50ms                       // Typing speed per character
// @speed 30ms                    // Faster typing
// @speed 100ms                   // Slower, more dramatic typing

@start 500ms                      // Delay before recording starts
// @start 0ms                     // Start immediately
// @start 1s                      // Longer pause before starting

@end 2s                           // How long to hold the final frame
// @end 500ms                     // Quick ending
// @end 5s                        // Long pause on final frame

@fps 10                           // Frames per second
// @fps 15                        // Smoother animation (larger file)
// @fps 5                         // Smaller file size


// -- Appearance --
@title "{name}"                   // Window title bar text
// @title "My Awesome CLI"        // Custom title
// @title ""                      // No title

@theme "mocha"                    // Color theme (see all options below)
// @theme "latte"                 // Light theme (Catppuccin Latte)
// @theme "frappe"                // Medium dark (Catppuccin Frappe)
// @theme "macchiato"             // Medium dark (Catppuccin Macchiato)
// @theme "dracula"               // Dark purple
// @theme "nord"                  // Arctic blue
// @theme "tokyo"                 // Tokyo Night
// @theme "gruvbox"               // Retro warm

@cursor "block"                   // Cursor style
// @cursor "bar"                  // Thin vertical bar |
// @cursor "underline"            // Underline cursor _

@radius 10                        // Corner radius (px), 0 = sharp corners
// @radius 0                      // Sharp corners
// @radius 20                     // More rounded


// -- Advanced Options (uncomment to use) --

// @prompt "$ "                   // Custom prompt (default: user@dir $)
// @prompt ">>> "                 // Python-style prompt
// @prompt "> "                   // Minimal prompt

// @bare                          // Remove window chrome (no title bar/buttons)

// @native                        // Preserve TUI app's original colors

// @radius-outer 12               // Outer GIF corner radius (independent)
// @radius-inner 8                // Inner window corner radius (independent)

// @loop 0                        // Loop forever (default)
// @loop 1                        // Play once, no loop
// @loop 3                        // Loop 3 times then stop

// @quality 2                     // Render quality (default: 2)
// @quality 1                     // Fast render, lower quality
// @quality 3                     // Ultra quality, slower render


// ================================ SCRIPT ====================================
//
// SYNTAX QUICK REFERENCE:
//
//   -> "text"          Type text character by character
//   >>                 Press Enter
//   -> "text" >>       Type text and press Enter (shorthand)
//   ~500ms             Wait for 500 milliseconds
//   ~2s                Wait for 2 seconds
//   ~1500              Wait for 1500ms (bare number = ms)
//   key "escape"       Press a special key (for TUI apps)
//   key "ctrl+c"       Press a key combination
//
// SPECIAL KEYS:
//   Navigation:  up, down, left, right, home, end, pageup, pagedown
//   Editing:     backspace, delete, tab, space
//   Control:     escape, enter, return
//   Function:    f1, f2, f3 ... f12
//   Modifiers:   ctrl+<key>, alt+<key>, shift+<key>
//
// ============================================================================


// -------------------- YOUR SCRIPT STARTS HERE --------------------

// Simple echo command
-> "echo Hello, World!" >>
~1s

// List files
-> "ls -la" >>
~2s


// -------------------- MORE EXAMPLES (uncomment to try) --------------------

/*
// Multiple commands in sequence
-> "pwd" >>
~500ms
-> "whoami" >>
~500ms
-> "date" >>
~1s
*/

/*
// Chain commands together
-> "mkdir demo && cd demo && touch file.txt" >>
~1s
-> "ls" >>
~1s
*/

/*
// Show help output
-> "python --help" >>
~3s
*/

/*
// Git workflow
-> "git status" >>
~1s
-> "git add ." >>
~500ms
-> "git commit -m \\"Initial commit\\"" >>
~1s
-> "git log --oneline -3" >>
~2s
*/

/*
// Docker example
-> "docker ps" >>
~1s
-> "docker images" >>
~2s
*/


// -------------------- TUI APP EXAMPLES --------------------
//
// For TUI apps (vim, htop, fzf, etc.), use ONE of these approaches:
//   1. Default mode + @native flag   (captures PTY output with colors)
//   2. --terminal flag               (screen captures your actual terminal)
//

/*
// VIM EXAMPLE
// Run with: termgif {name} --native
// Or with:  termgif {name} --terminal

-> "vim hello.txt" >>
~1s
key "i"                           // Enter insert mode
-> "Hello from Vim!"
~500ms
key "escape"                      // Back to normal mode
-> ":wq" >>                       // Save and quit
~1s
*/

/*
// HTOP EXAMPLE
// Run with: termgif {name} --native

-> "htop" >>
~2s
key "F6"                          // Open sort menu
~1s
key "down"
key "down"
key "enter"
~2s
key "q"                           // Quit
~500ms
*/

/*
// FZF EXAMPLE
// Run with: termgif {name} --terminal

-> "ls | fzf" >>
~1s
-> "main"                         // Type to filter
~500ms
key "down"
key "down"
key "enter"                       // Select
~1s
*/

/*
// LAZYGIT EXAMPLE
// Run with: termgif {name} --native

-> "lazygit" >>
~2s
key "j"                           // Move down
key "j"
~500ms
key "enter"                       // Open details
~1s
key "q"                           // Quit
~500ms
*/
'''

HELP_TEXT = """
[bold cyan]termgif[/] - Dead simple terminal GIF recorder

[bold]Usage:[/]
  termgif [dim]<script.tg>[/]            Record a script to GIF
  termgif record [dim]<script.tg>[/]     Same as above
  termgif create [dim]<script.tg>[/]     Create a new script from template

[bold]Options:[/]
  -o, --output [dim]<path>[/]    Override output GIF path
  -b, --bare             No window chrome, just terminal
  -s, --simulate         Fake output (don't run real commands)
  -t, --terminal         Capture YOUR terminal window (screen record)
  -n, --native           Preserve TUI app's native colors (don't apply theme)
  -v, --version          Show version
  -h, --help             Show this help

[bold]Config Directives:[/]
  @output "demo.gif"       [dim]# output file[/]
  @size 80x24              [dim]# terminal size (WxH)[/]
  @font 16                 [dim]# font size (pixels)[/]
  @padding 20              [dim]# padding around content[/]
  @speed 50ms              [dim]# typing speed[/]
  @start 500ms             [dim]# initial delay[/]
  @end 2s                  [dim]# final frame hold[/]
  @fps 10                  [dim]# frames per second[/]
  @title "Demo"            [dim]# window title[/]
  @theme "mocha"           [dim]# color theme[/]
  @cursor "block"          [dim]# block/bar/underline[/]
  @prompt "$ "             [dim]# custom prompt[/]
  @bare                    [dim]# no window chrome[/]
  @radius 10               [dim]# corner radius (both)[/]
  @radius-outer 12         [dim]# outer GIF edge[/]
  @radius-inner 8          [dim]# inner window[/]
  @native                  [dim]# preserve TUI colors[/]
  @loop 0                  [dim]# 0=infinite, N=times[/]
  @quality 2               [dim]# 1=fast, 2=smooth, 3=ultra[/]

[bold]Script Actions:[/]
  -> "text"                [dim]# type text[/]
  >>                       [dim]# press enter[/]
  -> "text" >>             [dim]# type + enter[/]
  ~1s                      [dim]# wait (500ms, 1s, 2.5s)[/]
  key "escape"             [dim]# press key (--terminal only)[/]
  key "ctrl+c"             [dim]# key combo (--terminal only)[/]
  // comment               [dim]# single-line comment[/]

[bold]Themes:[/]
  mocha, latte, frappe, macchiato, dracula, nord, tokyo, gruvbox

[bold]Example:[/]
  termgif create demo      [dim]# creates demo.tg[/]
  termgif demo             [dim]# runs real commands -> demo.gif[/]
  termgif demo -s          [dim]# simulated (fake output)[/]
  termgif demo --terminal  [dim]# screen captures YOUR terminal[/]

[dim]v{version}[/]  |  github.com/aayushadhikari7/termgif [dim](star if useful!)[/]
"""

SCRIPT_NOT_FOUND = """
[bold red]File not found:[/] {path}

[bold]To create a new script:[/]
  termgif create {path}

[bold]Then record it:[/]
  termgif {path}
"""


def show_help():
    """Show help information."""
    console.print(HELP_TEXT.format(version=__version__))


def record(script_path: Path, output: Path | None = None, bare: bool = False, simulate: bool = False, terminal: bool = False, native: bool = False):
    """Record a script to GIF."""
    if terminal:
        # Screen capture mode - captures your actual terminal
        if not HAS_CAPTURE:
            console.print("[red]Error:[/] --terminal requires screen capture support (Windows/macOS only)")
            raise typer.Exit(1)

        console.print(f"[blue]Recording terminal[/] {script_path}")
        console.print("[dim]Screen capturing your terminal...[/]\n")

        try:
            out_path = record_terminal(script_path, output)
            console.print(f"\n[green]Done![/] Saved to {out_path}")
        except Exception as e:
            console.print(f"\n[red]Error:[/] {e}")
            raise typer.Exit(1)

    elif simulate:
        # Simulated mode - fake output
        mode = " [dim](bare)[/]" if bare else ""
        console.print(f"[blue]Recording (simulated)[/] {script_path}{mode}")

        try:
            out_path = record_script(script_path, output, bare)
            console.print(f"[green]Done![/] Saved to {out_path}")
        except Exception as e:
            console.print(f"[red]Error:[/] {e}")
            raise typer.Exit(1)

    else:
        # Default - run real commands
        mode = " [dim](bare)[/]" if bare else ""
        native_mode = " [dim](native colors)[/]" if native else ""
        console.print(f"[blue]Recording[/] {script_path}{mode}{native_mode}")
        console.print("[dim]Running commands...[/]\n")

        try:
            out_path = record_live(script_path, output, native_colors=native)
            console.print(f"\n[green]Done![/] Saved to {out_path}")
        except Exception as e:
            console.print(f"\n[red]Error:[/] {e}")
            raise typer.Exit(1)


def create(script_path: Path):
    """Create a new script from template."""
    if script_path.exists():
        console.print(f"[red]Error:[/] {script_path} already exists")
        raise typer.Exit(1)

    name = script_path.stem
    content = BOILERPLATE.format(name=name)
    script_path.write_text(content)

    console.print(f"[green]Created[/] {script_path}")
    console.print(f"\n[dim]Edit it, then run:[/] termgif {script_path}")


def main():
    """Main entry point."""
    args = sys.argv[1:]

    # Check for first run welcome
    _check_first_run()

    # No arguments - show help
    if not args:
        show_help()
        return

    # Handle flags
    if args[0] in ("-h", "--help"):
        show_help()
        return

    if args[0] in ("-v", "--version"):
        console.print(f"termgif {__version__}")
        return

    # termgif create <script.tg>
    if args[0] == "create":
        if len(args) < 2:
            console.print("[red]Error:[/] Missing filename")
            console.print("Usage: termgif create <script.tg>")
            raise typer.Exit(1)

        path = Path(args[1])
        if not path.suffix:
            path = path.with_suffix(".tg")
        create(path)
        return

    # termgif record <script.tg> [-o output.gif] (optional "record" keyword)
    if args[0] == "record":
        if len(args) < 2:
            console.print("[red]Error:[/] Missing filename")
            console.print("Usage: termgif record <script.tg>")
            raise typer.Exit(1)
        args = args[1:]  # shift args

    # termgif <script.tg> [-o output.gif] [--bare]
    script_path = Path(args[0])

    # Auto-add .tg extension if missing
    if not script_path.suffix:
        script_path = script_path.with_suffix(".tg")

    # Check if file exists
    if not script_path.exists():
        console.print(SCRIPT_NOT_FOUND.format(path=script_path))
        raise typer.Exit(1)

    # Parse optional flags
    output = None
    bare = False
    simulate = False
    terminal = False
    native = False
    i = 1
    while i < len(args):
        if args[i] in ("-o", "--output") and i + 1 < len(args):
            # Strip quotes that Windows cmd may pass through
            output_arg = args[i + 1].strip('"').strip("'")
            output = Path(output_arg)
            i += 2
        elif args[i] in ("--bare", "-b"):
            bare = True
            i += 1
        elif args[i] in ("--simulate", "--sim", "-s"):
            simulate = True
            i += 1
        elif args[i] in ("--terminal", "-t"):
            terminal = True
            i += 1
        elif args[i] in ("--native", "-n"):
            native = True
            i += 1
        else:
            i += 1

    record(script_path, output, bare, simulate, terminal, native)


if __name__ == "__main__":
    main()
