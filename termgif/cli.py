"""CLI for termgif - comprehensive terminal recording studio."""
import sys
import time
import webbrowser
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .templates import list_templates, render_template

console = Console()
GITHUB_URL = "https://github.com/aayushadhikari7/termgif"


def _check_first_run():
    """Check if this is the first run and show welcome message."""
    marker = Path.home() / ".termgif_welcomed"
    if not marker.exists():
        console.print(Panel(
            f"[bold cyan]Welcome to termgif v{__version__}![/]\n\n"
            f"Terminal recording studio - GIF, MP4, WebP, and more.\n\n"
            f"[dim]Like it? Give us a star:[/] [link={GITHUB_URL}]{GITHUB_URL}[/link]",
            title="termgif",
            border_style="cyan"
        ))
        try:
            webbrowser.open(GITHUB_URL)
        except Exception:
            pass
        marker.touch()
        console.print()


# Comprehensive boilerplate for new scripts
BOILERPLATE = '''// {name}.tg - termgif recording script
// Run: termgif {name}
//
// Modes:
//   termgif {name}             <- runs real commands (default)
//   termgif {name} --simulate  <- safe mode, typing only, no execution
//   termgif {name} -f mp4      <- output as MP4 instead of GIF
//   termgif {name} --watch     <- auto-regenerate on save

// ============================================================================
// CONFIGURATION - Customize your recording
// ============================================================================

@output "{name}.gif"
@title "{name}"
@theme "mocha"               // mocha, dracula, nord, tokyo, gruvbox, latte

// Terminal size & appearance
// @size 80x24              // terminal size (columns x rows)
// @font 14                 // font size in pixels
// @padding 20              // padding around content
// @quality 2               // render quality (1=fast, 2=smooth, 3=ultra)

// Prompt customization (customize your terminal prompt!)
// @user "demo"             // username (default: your system username)
// @hostname "myproject"    // folder/hostname (default: current directory)
// @symbol "$"              // prompt symbol: $ for user, # for root, > etc.
// @prompt ">>> "           // OR set entire custom prompt (overrides above)

// Timing
// @fps 10                  // frames per second
// @speed 40ms              // typing speed (lower = faster/smoother)
// @start 500ms             // delay before first action
// @end 2s                  // delay after last action

// Output format
// @format "gif"            // gif, webp, mp4, webm, apng, svg

// Window style
// @bare                    // no window chrome (border/title)
// @radius 10               // corner radius (0 = sharp corners)
// @cursor "block"          // cursor style: block, bar, underline

// ============================================================================
// ACTIONS - Your commands go here
// ============================================================================

// Basic syntax:
//   -> "text"     <- type text
//   >>            <- press Enter
//   -> "text" >>  <- type and press Enter
//   ~1s           <- wait 1 second
//   ~500ms        <- wait 500 milliseconds

// Example commands (edit these!)
-> "echo Hello from termgif!" >>
~1s

-> "echo Your commands go here" >>
~1s

// Uncomment below for more examples:

// -> "ls -la" >>
// ~2s

// -> "pwd" >>
// ~1s

// -> "date" >>
// ~1s

// ============================================================================
// TUI APPS (vim, htop, etc.) - requires: termgif {name} --terminal --native
// ============================================================================

// Uncomment for TUI app recording:
// @native                   // preserve app colors

// key "escape"              // press Escape
// key "enter"               // press Enter
// key "up" / "down"         // arrow keys
// key "ctrl+c"              // Ctrl+C

// ============================================================================
// MORE TEMPLATES: termgif templates
// CREATE FROM TEMPLATE: termgif create myname --template git
// ============================================================================
'''


HELP_TEXT = """
[bold cyan]termgif[/] - Terminal recording studio

[bold]Usage:[/]
  termgif [dim]<script.tg>[/]              Record a script
  termgif record [dim]<script.tg>[/]       Same as above
  termgif create [dim]<name>[/]            Create new script
  termgif live                       Live recording mode
  termgif templates                  List available templates
  termgif preview [dim]<file>[/]           Preview recording (--play to animate)
  termgif info [dim]<file>[/]              Show file info

[bold]Editing:[/]
  termgif trim [dim]<file>[/]              Trim start/end
  termgif speed [dim]<file> <2x>[/]        Change speed
  termgif concat [dim]<files...>[/]        Concatenate recordings
  termgif overlay [dim]<file>[/]           Add watermark/caption

[bold]Import/Export:[/]
  termgif import [dim]<file.cast>[/]       Import asciinema cast file
  termgif export [dim]<script.tg>[/]       Export script to asciinema format

[bold]Sharing:[/]
  termgif upload [dim]<file>[/]            Upload to sharing service (catbox/imgur/giphy)

[bold]Configuration:[/]
  termgif config                     Show current configuration
  termgif config --init              Create default config file
  termgif config --edit              Edit config file in editor

[bold]Recording Options:[/]
  -o, --output [dim]<path>[/]    Output path
  -f, --format [dim]<fmt>[/]     Output format (gif, webp, mp4, webm, apng, svg)
  -b, --bare             No window chrome
  -s, --simulate         Don't run commands
  -t, --terminal         Screen capture mode
  -n, --native           Preserve TUI colors
  -w, --watch            Auto-regenerate on changes

[bold]Formats:[/]
  gif, webp, mp4, webm, apng, svg, frames, cast (asciinema)

[bold]Themes:[/]
  mocha, latte, frappe, macchiato, dracula, nord, tokyo, gruvbox, catppuccin

[bold]Config Directives:[/]
  @output, @size, @font, @speed, @title, @theme, @fps, @quality
  @format, @bitrate, @codec, @crf, @dither, @colors, @lossy
  @watermark, @caption, @prompt, @cursor, @radius, @native, @bare

[bold]Script Actions:[/]
  -> "text"              Type text
  >>                     Press enter
  -> "text" >>           Type + enter
  ~1s                    Wait (500ms, 1s, 2.5s)
  key "escape"           Press key

[bold]Examples:[/]
  termgif create demo --template git    Create from template
  termgif demo -f mp4                   Record to MP4
  termgif demo --watch                  Auto-regenerate
  termgif live -o session.gif           Live recording
  termgif trim demo.gif -s 2s -e -1s    Cut start/end
  termgif import session.cast -f mp4    Convert asciinema to MP4
  termgif upload demo.gif               Upload to Catbox
  termgif preview demo.gif --play       Play GIF in terminal

[dim]v{version}[/]  |  github.com/aayushadhikari7/termgif
"""


def show_help():
    """Show help information."""
    console.print(HELP_TEXT.format(version=__version__))


def cmd_record(
    script_path: Path,
    output: Path | None = None,
    format: str | None = None,
    bare: bool = False,
    simulate: bool = False,
    terminal: bool = False,
    native: bool = False,
    watch: bool = False,
):
    """Record a script to output file."""
    from .core import record_live, record_terminal
    from .core.simulated import record_script

    # Watch mode
    if watch:
        return cmd_watch(script_path, output, format, bare, simulate, terminal, native)

    # Determine output path and format
    from .parser import parse_script
    config, _ = parse_script(script_path)

    if output:
        output_path = output
    elif config.output:
        output_path = Path(config.output)
    else:
        output_path = script_path.with_suffix(".gif")

    # Format override
    if format:
        config.format = format
        ext = f".{format}"
        if not output_path.suffix.lower() == ext:
            output_path = output_path.with_suffix(ext)

    if terminal:
        # Screen capture mode
        from .core.terminal import HAS_CAPTURE
        if not HAS_CAPTURE:
            console.print("[red]Error:[/] --terminal requires screen capture support (Windows/macOS only)")
            raise typer.Exit(1)

        console.print(f"[blue]Recording terminal[/] {script_path}")
        console.print("[dim]Screen capturing your terminal...[/]\n")

        try:
            out_path = record_terminal(script_path, output_path)
            console.print(f"\n[green]Done![/] Saved to {out_path}")
        except Exception as e:
            console.print(f"\n[red]Error:[/] {e}")
            raise typer.Exit(1)

    elif simulate:
        # Simulated mode
        mode = " [dim](bare)[/]" if bare else ""
        console.print(f"[blue]Recording (simulated)[/] {script_path}{mode}")

        try:
            out_path = record_script(script_path, output_path, bare)
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
            out_path = record_live(script_path, output_path, native_colors=native)
            console.print(f"\n[green]Done![/] Saved to {out_path}")
        except Exception as e:
            console.print(f"\n[red]Error:[/] {e}")
            raise typer.Exit(1)


def cmd_create(name: str, template: str | None = None):
    """Create a new script from template."""
    script_path = Path(name)
    if not script_path.suffix:
        script_path = script_path.with_suffix(".tg")

    if script_path.exists():
        console.print(f"[red]Error:[/] {script_path} already exists")
        raise typer.Exit(1)

    if template:
        try:
            content = render_template(template, name=script_path.stem, title=script_path.stem.title())
        except ValueError as e:
            console.print(f"[red]Error:[/] {e}")
            raise typer.Exit(1)
    else:
        content = BOILERPLATE.format(name=script_path.stem)

    script_path.write_text(content)

    console.print(f"[green]Created[/] {script_path}")
    if template:
        console.print(f"[dim]Using template:[/] {template}")
    console.print(f"\n[dim]Edit it, then run:[/] termgif {script_path}")


def cmd_live(
    output: str = "session.gif",
    fps: int = 10,
    duration: int | None = None,
):
    """Start live recording session."""
    from .core.session import record_live_session

    console.print("[bold cyan]termgif live recording[/]")

    try:
        output_path = record_live_session(
            output=output,
            fps=fps,
            duration=duration,
        )
        console.print(f"\n[green]Saved to {output_path}[/]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Recording stopped[/]")
    except Exception as e:
        console.print(f"\n[red]Error:[/] {e}")
        raise typer.Exit(1)


def cmd_watch(
    script_path: Path,
    output: Path | None = None,
    format: str | None = None,
    bare: bool = False,
    simulate: bool = False,
    terminal: bool = False,
    native: bool = False,
):
    """Watch script file and auto-regenerate on change."""
    console.print(f"[cyan]Watching[/] {script_path} for changes...")
    console.print("[dim]Press Ctrl+C to stop[/]\n")

    last_mtime = script_path.stat().st_mtime

    try:
        while True:
            current_mtime = script_path.stat().st_mtime
            if current_mtime > last_mtime:
                console.print(f"[blue]Change detected, regenerating...[/]")
                try:
                    cmd_record(script_path, output, format, bare, simulate, terminal, native, watch=False)
                except Exception as e:
                    console.print(f"[red]Error:[/] {e}")
                last_mtime = current_mtime
            time.sleep(0.5)
    except KeyboardInterrupt:
        console.print("\n[yellow]Watch stopped[/]")


def cmd_templates():
    """List available templates."""
    templates = list_templates()

    table = Table(title="Available Templates")
    table.add_column("Name", style="cyan")
    table.add_column("Description")

    descriptions = {
        "basic": "Simple echo and ls commands",
        "git": "Git workflow (status, add, commit, push)",
        "npm": "npm workflow (init, install, list)",
        "docker": "Docker commands (ps, images, build, run)",
        "python": "Python REPL demo",
        "pip": "pip workflow (install, list, show)",
        "vim": "Vim editing demo (requires --native)",
        "htop": "htop system monitor (requires --native)",
        "fzf": "fzf fuzzy finder (requires --terminal)",
        "lazygit": "lazygit demo (requires --native)",
        "api": "API testing with curl and jq",
    }

    for name in templates:
        table.add_row(name, descriptions.get(name, ""))

    console.print(table)
    console.print("\n[dim]Usage:[/] termgif create demo --template git")


def cmd_preview(file_path: Path, play: bool = False, script: bool = False):
    """Preview a recording in the terminal."""
    from .preview import play_gif_in_terminal, preview_script, print_file_info

    if not file_path.exists():
        console.print(f"[red]Error:[/] File not found: {file_path}")
        raise typer.Exit(1)

    try:
        if script or file_path.suffix.lower() in ('.tg', '.tape'):
            # Preview script file
            preview_script(file_path, console)
        elif play:
            # Play animation in terminal
            play_gif_in_terminal(file_path)
        else:
            # Show file info
            print_file_info(file_path, console)
            console.print("\n[dim]Use --play to play animation in terminal[/]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Preview stopped[/]")
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)


def cmd_info(file_path: Path):
    """Show information about a file."""
    from PIL import Image

    if not file_path.exists():
        console.print(f"[red]Error:[/] File not found: {file_path}")
        raise typer.Exit(1)

    try:
        img = Image.open(file_path)

        # Count frames and total duration
        frames = 0
        total_duration = 0

        try:
            while True:
                frames += 1
                total_duration += img.info.get('duration', 100)
                img.seek(img.tell() + 1)
        except EOFError:
            pass

        file_size = file_path.stat().st_size

        table = Table(title=f"File Info: {file_path.name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value")

        table.add_row("Format", file_path.suffix.upper().lstrip('.'))
        table.add_row("Size", f"{img.size[0]}x{img.size[1]}")
        table.add_row("Frames", str(frames))
        table.add_row("Duration", f"{total_duration/1000:.1f}s")
        table.add_row("File size", f"{file_size/1024:.1f} KB")

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)


def cmd_trim(
    file_path: Path,
    output: Path | None = None,
    start: str = "0",
    end: str | None = None,
):
    """Trim a recording."""
    from .editor import trim_recording
    from .config import parse_duration

    start_ms = parse_duration(start)
    end_ms = parse_duration(end) if end else None

    try:
        out_path = trim_recording(file_path, output, start_ms, end_ms)
        console.print(f"[green]Trimmed![/] Saved to {out_path}")
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)


def cmd_speed(file_path: Path, speed: str, output: Path | None = None):
    """Change playback speed."""
    from .editor import change_speed

    try:
        speed_val = float(speed.rstrip('x'))
    except ValueError:
        console.print(f"[red]Error:[/] Invalid speed: {speed}")
        raise typer.Exit(1)

    try:
        out_path = change_speed(file_path, output, speed_val)
        console.print(f"[green]Speed changed![/] Saved to {out_path}")
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)


def cmd_concat(files: list[Path], output: Path):
    """Concatenate recordings."""
    from .editor import concatenate

    try:
        out_path = concatenate(files, output)
        console.print(f"[green]Concatenated {len(files)} files![/] Saved to {out_path}")
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)


def cmd_overlay(
    file_path: Path,
    output: Path | None = None,
    text: str | None = None,
    watermark: Path | None = None,
    position: str = "bottom-right",
    opacity: float = 0.5,
):
    """Add overlay (watermark or caption)."""
    from .editor import add_watermark, add_caption

    try:
        if watermark:
            out_path = add_watermark(file_path, watermark, output, position, opacity)
            console.print(f"[green]Watermark added![/] Saved to {out_path}")
        elif text:
            out_path = add_caption(file_path, text, output, position)
            console.print(f"[green]Caption added![/] Saved to {out_path}")
        else:
            console.print("[red]Error:[/] Specify --text or --watermark")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)


def cmd_import(
    cast_path: Path,
    output: Path | None = None,
    format: str = "gif",
):
    """Import an asciinema cast file and convert to another format."""
    from .exporters.asciinema import render_cast_to_frames
    from .exporters import get_exporter
    from .config import TapeConfig

    if not cast_path.exists():
        console.print(f"[red]Error:[/] File not found: {cast_path}")
        raise typer.Exit(1)

    if output is None:
        output = cast_path.with_suffix(f".{format}")

    console.print(f"[blue]Importing[/] {cast_path}")

    try:
        frames, durations = render_cast_to_frames(cast_path)
        config = TapeConfig(format=format)

        exporter_cls = get_exporter(format)
        if exporter_cls is None:
            console.print(f"[red]Error:[/] Unknown format: {format}")
            raise typer.Exit(1)

        exporter = exporter_cls(frames, durations, config)
        out_path = exporter.export(output)

        console.print(f"[green]Imported![/] Saved to {out_path}")

    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)


def cmd_export(
    script_path: Path,
    output: Path | None = None,
):
    """Export a script to asciinema cast format."""
    from .parser import parse_script
    from .exporters.asciinema import AsciinemaTextExporter

    if not script_path.exists():
        console.print(f"[red]Error:[/] File not found: {script_path}")
        raise typer.Exit(1)

    if output is None:
        output = script_path.with_suffix(".cast")

    console.print(f"[blue]Exporting[/] {script_path} to asciinema format")

    try:
        config, actions = parse_script(script_path)

        exporter = AsciinemaTextExporter(
            width=config.width,
            height=config.height,
            title=config.title,
        )
        exporter.start()

        # Convert actions to output events
        for action in actions:
            action_type = type(action).__name__

            if action_type == "TypeAction":
                exporter.add_output(action.text)
            elif action_type == "EnterAction":
                exporter.add_output("\r\n")
            elif action_type == "SleepAction":
                import time
                time.sleep(action.duration_ms / 1000.0)
            elif action_type == "KeyAction":
                # Map common keys to escape sequences
                key_map = {
                    "escape": "\x1b",
                    "tab": "\t",
                    "backspace": "\x7f",
                }
                exporter.add_output(key_map.get(action.key.lower(), ""))

        out_path = exporter.export(output)
        console.print(f"[green]Exported![/] Saved to {out_path}")

    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)


def cmd_upload(
    file_path: Path,
    service: str = "catbox",
):
    """Upload a file to a sharing service."""
    from .utils.share import upload, get_available_services, ShareError
    from .utils.config_file import get_config_value

    if not file_path.exists():
        console.print(f"[red]Error:[/] File not found: {file_path}")
        raise typer.Exit(1)

    console.print(f"[blue]Uploading[/] {file_path} to {service}...")

    try:
        # Get credentials from config
        kwargs = {}
        if service == "imgur":
            client_id = get_config_value("sharing.imgur_client_id")
            if not client_id:
                console.print("[red]Error:[/] Imgur client ID not configured")
                console.print("[dim]Set it in ~/.config/termgif/config.toml[/]")
                raise typer.Exit(1)
            kwargs["client_id"] = client_id

        elif service == "giphy":
            api_key = get_config_value("sharing.giphy_api_key")
            if not api_key:
                console.print("[red]Error:[/] Giphy API key not configured")
                console.print("[dim]Set it in ~/.config/termgif/config.toml[/]")
                raise typer.Exit(1)
            kwargs["api_key"] = api_key

        result = upload(file_path, service, **kwargs)
        console.print(f"[green]Uploaded![/]")
        console.print(f"\n[bold]URL:[/] {result['url']}")

        if result.get('delete_hash'):
            console.print(f"[dim]Delete hash: {result['delete_hash']}[/]")

    except ShareError as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)


def cmd_config(edit: bool = False, init: bool = False):
    """Show or edit configuration."""
    from .utils.config_file import (
        get_global_config_path, create_default_config, load_config
    )
    import subprocess

    config_path = get_global_config_path()

    if init:
        if config_path.exists():
            console.print(f"[yellow]Config already exists:[/] {config_path}")
        else:
            create_default_config(config_path)
            console.print(f"[green]Created config:[/] {config_path}")
        return

    if edit:
        if not config_path.exists():
            create_default_config(config_path)
            console.print(f"[green]Created config:[/] {config_path}")

        # Try to open in editor
        import os
        editor = os.environ.get("EDITOR", "notepad" if sys.platform == "win32" else "nano")
        try:
            subprocess.run([editor, str(config_path)])
        except Exception:
            console.print(f"[yellow]Could not open editor. Edit manually:[/]")
            console.print(f"  {config_path}")
        return

    # Show current config
    console.print(f"[bold]Config file:[/] {config_path}")

    if config_path.exists():
        config = load_config()
        console.print("\n[bold]Current settings:[/]")

        table = Table()
        table.add_column("Setting", style="cyan")
        table.add_column("Value")

        table.add_row("defaults.theme", config.defaults.theme)
        table.add_row("defaults.font_size", str(config.defaults.font_size))
        table.add_row("defaults.fps", str(config.defaults.fps))
        table.add_row("defaults.format", config.defaults.format)
        table.add_row("defaults.width", str(config.defaults.width))
        table.add_row("defaults.height", str(config.defaults.height))
        table.add_row("sharing.default_service", config.sharing.default_service)
        table.add_row("sharing.imgur_client_id", "***" if config.sharing.imgur_client_id else "(not set)")
        table.add_row("sharing.giphy_api_key", "***" if config.sharing.giphy_api_key else "(not set)")

        console.print(table)
        console.print("\n[dim]To edit: termgif config --edit[/]")
    else:
        console.print("[dim]No config file found.[/]")
        console.print("[dim]To create: termgif config --init[/]")


def main():
    """Main entry point."""
    args = sys.argv[1:]

    _check_first_run()

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

    # Commands
    cmd = args[0].lower()

    if cmd == "create":
        if len(args) < 2:
            console.print("[red]Error:[/] Missing filename")
            raise typer.Exit(1)
        name = args[1]
        template = None
        if len(args) > 2 and args[2] in ("--template", "-t"):
            template = args[3] if len(args) > 3 else None
        cmd_create(name, template)
        return

    if cmd == "live":
        output = "session.gif"
        fps = 10
        duration = None
        i = 1
        while i < len(args):
            if args[i] in ("-o", "--output") and i + 1 < len(args):
                output = args[i + 1]
                i += 2
            elif args[i] in ("--fps",) and i + 1 < len(args):
                fps = int(args[i + 1])
                i += 2
            elif args[i] in ("--duration",) and i + 1 < len(args):
                duration = int(args[i + 1])
                i += 2
            else:
                i += 1
        cmd_live(output, fps, duration)
        return

    if cmd == "templates":
        cmd_templates()
        return

    if cmd == "preview":
        if len(args) < 2:
            console.print("[red]Error:[/] Missing file path")
            raise typer.Exit(1)
        file_path = Path(args[1])
        play = "--play" in args or "-p" in args
        script = "--script" in args
        cmd_preview(file_path, play, script)
        return

    if cmd == "import":
        if len(args) < 2:
            console.print("[red]Error:[/] Missing cast file path")
            raise typer.Exit(1)
        cast_path = Path(args[1])
        output = None
        format_type = "gif"
        i = 2
        while i < len(args):
            if args[i] in ("-o", "--output") and i + 1 < len(args):
                output = Path(args[i + 1])
                i += 2
            elif args[i] in ("-f", "--format") and i + 1 < len(args):
                format_type = args[i + 1]
                i += 2
            else:
                i += 1
        cmd_import(cast_path, output, format_type)
        return

    if cmd == "export":
        if len(args) < 2:
            console.print("[red]Error:[/] Missing script path")
            raise typer.Exit(1)
        script_path = Path(args[1])
        output = None
        if len(args) > 2 and args[2] in ("-o", "--output"):
            output = Path(args[3]) if len(args) > 3 else None
        cmd_export(script_path, output)
        return

    if cmd == "upload":
        if len(args) < 2:
            console.print("[red]Error:[/] Missing file path")
            raise typer.Exit(1)
        file_path = Path(args[1])
        service = "catbox"
        if len(args) > 2 and args[2] in ("--service", "-s"):
            service = args[3] if len(args) > 3 else "catbox"
        elif len(args) > 2 and args[2] not in ("-o", "--output"):
            service = args[2]
        cmd_upload(file_path, service)
        return

    if cmd == "config":
        edit = "--edit" in args or "-e" in args
        init = "--init" in args
        cmd_config(edit, init)
        return

    if cmd == "info":
        if len(args) < 2:
            console.print("[red]Error:[/] Missing file path")
            raise typer.Exit(1)
        cmd_info(Path(args[1]))
        return

    if cmd == "trim":
        if len(args) < 2:
            console.print("[red]Error:[/] Missing file path")
            raise typer.Exit(1)
        file_path = Path(args[1])
        output = None
        start = "0"
        end = None
        i = 2
        while i < len(args):
            if args[i] in ("-o", "--output") and i + 1 < len(args):
                output = Path(args[i + 1])
                i += 2
            elif args[i] in ("-s", "--start") and i + 1 < len(args):
                start = args[i + 1]
                i += 2
            elif args[i] in ("-e", "--end") and i + 1 < len(args):
                end = args[i + 1]
                i += 2
            else:
                i += 1
        cmd_trim(file_path, output, start, end)
        return

    if cmd == "speed":
        if len(args) < 3:
            console.print("[red]Error:[/] Usage: termgif speed <file> <speed>")
            raise typer.Exit(1)
        file_path = Path(args[1])
        speed = args[2]
        output = None
        if len(args) > 3 and args[3] in ("-o", "--output"):
            output = Path(args[4]) if len(args) > 4 else None
        cmd_speed(file_path, speed, output)
        return

    if cmd == "concat":
        # Find all file args until -o
        files = []
        output = None
        i = 1
        while i < len(args):
            if args[i] in ("-o", "--output") and i + 1 < len(args):
                output = Path(args[i + 1])
                i += 2
            else:
                files.append(Path(args[i]))
                i += 1
        if not files or not output:
            console.print("[red]Error:[/] Usage: termgif concat <file1> <file2> ... -o <output>")
            raise typer.Exit(1)
        cmd_concat(files, output)
        return

    if cmd == "overlay":
        if len(args) < 2:
            console.print("[red]Error:[/] Missing file path")
            raise typer.Exit(1)
        file_path = Path(args[1])
        output = None
        text = None
        watermark = None
        position = "bottom-right"
        opacity = 0.5
        i = 2
        while i < len(args):
            if args[i] in ("-o", "--output") and i + 1 < len(args):
                output = Path(args[i + 1])
                i += 2
            elif args[i] in ("--text",) and i + 1 < len(args):
                text = args[i + 1]
                i += 2
            elif args[i] in ("--watermark",) and i + 1 < len(args):
                watermark = Path(args[i + 1])
                i += 2
            elif args[i] in ("--position",) and i + 1 < len(args):
                position = args[i + 1]
                i += 2
            elif args[i] in ("--opacity",) and i + 1 < len(args):
                opacity = float(args[i + 1])
                i += 2
            else:
                i += 1
        cmd_overlay(file_path, output, text, watermark, position, opacity)
        return

    # Record command (explicit or implicit)
    if cmd == "record":
        if len(args) < 2:
            console.print("[red]Error:[/] Missing filename")
            raise typer.Exit(1)
        args = args[1:]
        cmd = args[0]

    # Default: record a script
    script_path = Path(cmd)
    if not script_path.suffix:
        script_path = script_path.with_suffix(".tg")

    if not script_path.exists():
        console.print(f"[red]File not found:[/] {script_path}")
        console.print(f"\n[dim]To create:[/] termgif create {script_path}")
        raise typer.Exit(1)

    # Parse flags
    output = None
    format_type = None
    bare = False
    simulate = False
    terminal = False
    native = False
    watch = False

    i = 1
    while i < len(args):
        if args[i] in ("-o", "--output") and i + 1 < len(args):
            output = Path(args[i + 1].strip('"').strip("'"))
            i += 2
        elif args[i] in ("-f", "--format") and i + 1 < len(args):
            format_type = args[i + 1]
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
        elif args[i] in ("--watch", "-w"):
            watch = True
            i += 1
        else:
            i += 1

    cmd_record(script_path, output, format_type, bare, simulate, terminal, native, watch)


if __name__ == "__main__":
    main()
