"""Color themes for terminal rendering.

Includes popular terminal color schemes like Catppuccin, Dracula, Nord, etc.
"""

# Color themes dictionary
# Each theme contains:
# - Base colors: base, mantle, crust (backgrounds)
# - Surface colors: surface0, surface1, surface2 (borders, overlays)
# - Text colors: text, subtext1, subtext0 (main text, muted text)
# - Accent colors: red, yellow, green, blue, lavender, mauve, teal

THEMES = {
    "mocha": {  # Catppuccin Mocha (default)
        "base": "#1e1e2e", "mantle": "#181825", "crust": "#11111b",
        "surface0": "#313244", "surface1": "#45475a", "surface2": "#585b70",
        "text": "#cdd6f4", "subtext1": "#bac2de", "subtext0": "#a6adc8",
        "red": "#f38ba8", "yellow": "#f9e2af", "green": "#a6e3a1",
        "blue": "#89b4fa", "lavender": "#b4befe", "mauve": "#cba6f7", "teal": "#94e2d5",
    },
    "latte": {  # Catppuccin Latte (light theme)
        "base": "#eff1f5", "mantle": "#e6e9ef", "crust": "#dce0e8",
        "surface0": "#ccd0da", "surface1": "#bcc0cc", "surface2": "#acb0be",
        "text": "#4c4f69", "subtext1": "#5c5f77", "subtext0": "#6c6f85",
        "red": "#d20f39", "yellow": "#df8e1d", "green": "#40a02b",
        "blue": "#1e66f5", "lavender": "#7287fd", "mauve": "#8839ef", "teal": "#179299",
    },
    "frappe": {  # Catppuccin Frappé
        "base": "#303446", "mantle": "#292c3c", "crust": "#232634",
        "surface0": "#414559", "surface1": "#51576d", "surface2": "#626880",
        "text": "#c6d0f5", "subtext1": "#b5bfe2", "subtext0": "#a5adce",
        "red": "#e78284", "yellow": "#e5c890", "green": "#a6d189",
        "blue": "#8caaee", "lavender": "#babbf1", "mauve": "#ca9ee6", "teal": "#81c8be",
    },
    "macchiato": {  # Catppuccin Macchiato
        "base": "#24273a", "mantle": "#1e2030", "crust": "#181926",
        "surface0": "#363a4f", "surface1": "#494d64", "surface2": "#5b6078",
        "text": "#cad3f5", "subtext1": "#b8c0e0", "subtext0": "#a5adcb",
        "red": "#ed8796", "yellow": "#eed49f", "green": "#a6da95",
        "blue": "#8aadf4", "lavender": "#b7bdf8", "mauve": "#c6a0f6", "teal": "#8bd5ca",
    },
    "dracula": {  # Dracula
        "base": "#282a36", "mantle": "#21222c", "crust": "#191a21",
        "surface0": "#44475a", "surface1": "#4d4f5c", "surface2": "#565761",
        "text": "#f8f8f2", "subtext1": "#e0e0e0", "subtext0": "#bfbfbf",
        "red": "#ff5555", "yellow": "#f1fa8c", "green": "#50fa7b",
        "blue": "#8be9fd", "lavender": "#bd93f9", "mauve": "#ff79c6", "teal": "#8be9fd",
    },
    "nord": {  # Nord
        "base": "#2e3440", "mantle": "#272c36", "crust": "#20242d",
        "surface0": "#3b4252", "surface1": "#434c5e", "surface2": "#4c566a",
        "text": "#eceff4", "subtext1": "#e5e9f0", "subtext0": "#d8dee9",
        "red": "#bf616a", "yellow": "#ebcb8b", "green": "#a3be8c",
        "blue": "#81a1c1", "lavender": "#b48ead", "mauve": "#b48ead", "teal": "#8fbcbb",
    },
    "tokyo": {  # Tokyo Night
        "base": "#1a1b26", "mantle": "#16161e", "crust": "#13131a",
        "surface0": "#24283b", "surface1": "#2f3549", "surface2": "#3b4261",
        "text": "#c0caf5", "subtext1": "#a9b1d6", "subtext0": "#9aa5ce",
        "red": "#f7768e", "yellow": "#e0af68", "green": "#9ece6a",
        "blue": "#7aa2f7", "lavender": "#bb9af7", "mauve": "#bb9af7", "teal": "#73daca",
    },
    "gruvbox": {  # Gruvbox Dark
        "base": "#282828", "mantle": "#1d2021", "crust": "#171717",
        "surface0": "#3c3836", "surface1": "#504945", "surface2": "#665c54",
        "text": "#ebdbb2", "subtext1": "#d5c4a1", "subtext0": "#bdae93",
        "red": "#fb4934", "yellow": "#fabd2f", "green": "#b8bb26",
        "blue": "#83a598", "lavender": "#d3869b", "mauve": "#d3869b", "teal": "#8ec07c",
    },
    "one-dark": {  # One Dark (Atom)
        "base": "#282c34", "mantle": "#21252b", "crust": "#1b1f23",
        "surface0": "#3e4451", "surface1": "#4b5263", "surface2": "#5c6370",
        "text": "#abb2bf", "subtext1": "#9da5b4", "subtext0": "#848b98",
        "red": "#e06c75", "yellow": "#e5c07b", "green": "#98c379",
        "blue": "#61afef", "lavender": "#c678dd", "mauve": "#c678dd", "teal": "#56b6c2",
    },
    "solarized-dark": {  # Solarized Dark
        "base": "#002b36", "mantle": "#00252e", "crust": "#001f27",
        "surface0": "#073642", "surface1": "#094352", "surface2": "#0b4f61",
        "text": "#839496", "subtext1": "#93a1a1", "subtext0": "#657b83",
        "red": "#dc322f", "yellow": "#b58900", "green": "#859900",
        "blue": "#268bd2", "lavender": "#6c71c4", "mauve": "#d33682", "teal": "#2aa198",
    },
    "solarized-light": {  # Solarized Light
        "base": "#fdf6e3", "mantle": "#eee8d5", "crust": "#e4ddc8",
        "surface0": "#d5ceba", "surface1": "#c5beac", "surface2": "#b5ae9e",
        "text": "#657b83", "subtext1": "#586e75", "subtext0": "#839496",
        "red": "#dc322f", "yellow": "#b58900", "green": "#859900",
        "blue": "#268bd2", "lavender": "#6c71c4", "mauve": "#d33682", "teal": "#2aa198",
    },
    "github-dark": {  # GitHub Dark
        "base": "#0d1117", "mantle": "#010409", "crust": "#000000",
        "surface0": "#161b22", "surface1": "#21262d", "surface2": "#30363d",
        "text": "#c9d1d9", "subtext1": "#b1bac4", "subtext0": "#8b949e",
        "red": "#ff7b72", "yellow": "#d29922", "green": "#3fb950",
        "blue": "#58a6ff", "lavender": "#a5d6ff", "mauve": "#bc8cff", "teal": "#39c5cf",
    },
    "material": {  # Material Dark
        "base": "#263238", "mantle": "#1e272c", "crust": "#171f23",
        "surface0": "#37474f", "surface1": "#455a64", "surface2": "#546e7a",
        "text": "#eeffff", "subtext1": "#cfd8dc", "subtext0": "#b0bec5",
        "red": "#ff5370", "yellow": "#ffcb6b", "green": "#c3e88d",
        "blue": "#82aaff", "lavender": "#c792ea", "mauve": "#f07178", "teal": "#89ddff",
    },
    "ayu-dark": {  # Ayu Dark
        "base": "#0a0e14", "mantle": "#060a0f", "crust": "#020509",
        "surface0": "#0d1016", "surface1": "#11151c", "surface2": "#1a1f29",
        "text": "#b3b1ad", "subtext1": "#9c9a97", "subtext0": "#73726e",
        "red": "#ff3333", "yellow": "#ff8f40", "green": "#c2d94c",
        "blue": "#59c2ff", "lavender": "#d2a6ff", "mauve": "#ffee99", "teal": "#95e6cb",
    },
}

# Default theme
DEFAULT_THEME = "mocha"


def get_theme(name: str) -> dict[str, str]:
    """Get a theme by name.

    Args:
        name: Theme name (case-insensitive)

    Returns:
        Theme color dictionary

    Raises:
        ValueError: If theme not found
    """
    name = name.lower()
    if name not in THEMES:
        available = ", ".join(sorted(THEMES.keys()))
        raise ValueError(f"Unknown theme '{name}'. Available themes: {available}")
    return THEMES[name]


def list_themes() -> list[str]:
    """Get list of available theme names.

    Returns:
        Sorted list of theme names
    """
    return sorted(THEMES.keys())


# ANSI color mapping to theme keys
ANSI_TO_THEME = {
    # Standard ANSI colors
    "black": "crust",
    "red": "red",
    "green": "green",
    "yellow": "yellow",
    "blue": "blue",
    "magenta": "mauve",
    "cyan": "teal",
    "white": "text",
    # Bright ANSI colors
    "bright_black": "surface2",
    "bright_red": "red",
    "bright_green": "green",
    "bright_yellow": "yellow",
    "bright_blue": "blue",
    "bright_magenta": "mauve",
    "bright_cyan": "teal",
    "bright_white": "text",
    # Default names
    "text": "text",
    "base": "base",
    "default": "text",
}


def resolve_color(color_name: str, theme: dict[str, str], is_foreground: bool = True) -> str:
    """Resolve an ANSI color name or hex color to a theme color or hex.

    Args:
        color_name: Color name (e.g., "red", "green", "text") or hex ("#rrggbb")
        theme: Theme color dictionary
        is_foreground: Whether this is a foreground color (affects defaults)

    Returns:
        Hex color string
    """
    # Already hex color
    if color_name.startswith("#"):
        return color_name

    # Map ANSI color to theme key
    theme_key = ANSI_TO_THEME.get(color_name, "text" if is_foreground else "base")
    return theme.get(theme_key, theme["text"] if is_foreground else theme["base"])
