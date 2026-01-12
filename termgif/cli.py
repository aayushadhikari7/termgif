"""CLI for termgif."""
import sys
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel

from . import __version__
from .recorder import record_script
from .capture import record_live, record_terminal, HAS_CAPTURE

console = Console()

BOILERPLATE = '''// =============================================
// {name}.tg - termgif script
// Run with: termgif {name}
// =============================================

// ------------------- CONFIG -------------------

// Output
@output "{name}.gif"

// Terminal size
@size 80x24                   // Width x Height in characters
@font 16                      // Font size in pixels
@padding 20                   // Padding around content

// Timing
@speed 50ms                   // Typing speed per character
@start 500ms                  // Delay before starting
@end 2s                       // Hold final frame
@fps 10                       // Frames per second (for --terminal)

// Appearance
@title "{name}"               // Window title
@theme "mocha"                // mocha, latte, frappe, macchiato, dracula, nord, tokyo, gruvbox
@cursor "block"               // block, bar, underline
// @prompt "$ "               // Custom prompt (default: auto)
// @bare                      // No window chrome

// Corners
@radius 10                    // Both inner & outer (0 = sharp)
// @radius-outer 12           // Outer GIF edge only
// @radius-inner 8            // Inner window only

// Advanced
@loop 0                       // 0 = infinite, 1 = once, N = N times
@quality 2                    // 1 = fast, 2 = smooth, 3 = ultra

// ------------------- SCRIPT -------------------
// Syntax:
//   -> "text"        Type text
//   >>               Press Enter
//   -> "text" >>     Type + Enter (shorthand)
//   ~1s              Wait (500ms, 1s, 2.5s)
//   // comment       Single-line comment
//   /* comment */    Multi-line comment

-> "echo Hello, {name}!" >>
~1s

-> "python --version" >>
~2s
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
  @loop 0                  [dim]# 0=infinite, N=times[/]
  @quality 2               [dim]# 1=fast, 2=smooth, 3=ultra[/]

[bold]Script Actions:[/]
  -> "text"                [dim]# type text[/]
  >>                       [dim]# press enter[/]
  -> "text" >>             [dim]# type + enter[/]
  ~1s                      [dim]# wait (500ms, 1s, 2.5s)[/]
  // comment               [dim]# single-line comment[/]

[bold]Themes:[/]
  mocha, latte, frappe, macchiato, dracula, nord, tokyo, gruvbox

[bold]Example:[/]
  termgif create demo      [dim]# creates demo.tg[/]
  termgif demo             [dim]# runs real commands -> demo.gif[/]
  termgif demo -s          [dim]# simulated (fake output)[/]
  termgif demo --terminal  [dim]# screen captures YOUR terminal[/]

[dim]v{version}[/]
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


def record(script_path: Path, output: Path | None = None, bare: bool = False, simulate: bool = False, terminal: bool = False):
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
        console.print(f"[blue]Recording[/] {script_path}{mode}")
        console.print("[dim]Running commands...[/]\n")

        try:
            out_path = record_live(script_path, output)
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
        else:
            i += 1

    record(script_path, output, bare, simulate, terminal)


if __name__ == "__main__":
    main()
