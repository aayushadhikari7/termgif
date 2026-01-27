"""Global and project configuration file support."""
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
import os

# Try to import tomllib (Python 3.11+) or tomli
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


@dataclass
class DefaultsConfig:
    """Default settings for recordings."""
    theme: str = "catppuccin"
    font_size: int = 16
    quality: int = 3
    fps: int = 10
    format: str = "gif"
    width: int = 80
    height: int = 24
    padding: int = 20
    shell: str = ""


@dataclass
class SharingConfig:
    """Sharing service credentials."""
    imgur_client_id: str = ""
    giphy_api_key: str = ""
    default_service: str = "catbox"


@dataclass
class PathsConfig:
    """Custom paths."""
    templates: str = ""
    output: str = ""


@dataclass
class GlobalConfig:
    """Global termgif configuration."""
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)
    sharing: SharingConfig = field(default_factory=SharingConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'defaults': asdict(self.defaults),
            'sharing': asdict(self.sharing),
            'paths': asdict(self.paths),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GlobalConfig':
        """Create from dictionary."""
        defaults = DefaultsConfig(**data.get('defaults', {}))
        sharing = SharingConfig(**data.get('sharing', {}))
        paths = PathsConfig(**data.get('paths', {}))
        return cls(defaults=defaults, sharing=sharing, paths=paths)


def get_config_dir() -> Path:
    """Get the configuration directory path.

    Returns:
        Path to config directory (~/.config/termgif on Unix, %APPDATA%/termgif on Windows)
    """
    if os.name == 'nt':
        # Windows
        base = Path(os.environ.get('APPDATA', Path.home()))
    else:
        # Unix-like
        base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))

    return base / 'termgif'


def get_global_config_path() -> Path:
    """Get the global configuration file path."""
    return get_config_dir() / 'config.toml'


def get_project_config_path(start_dir: Optional[Path] = None) -> Optional[Path]:
    """Find project configuration file by walking up the directory tree.

    Args:
        start_dir: Directory to start searching from (defaults to cwd)

    Returns:
        Path to .termgif.toml if found, None otherwise
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current = Path(start_dir).resolve()

    while current != current.parent:
        config_path = current / '.termgif.toml'
        if config_path.exists():
            return config_path
        current = current.parent

    return None


def parse_toml(path: Path) -> dict:
    """Parse a TOML file.

    Args:
        path: Path to the TOML file

    Returns:
        Parsed dictionary

    Raises:
        ImportError: If toml parsing library not available
        FileNotFoundError: If file doesn't exist
    """
    if tomllib is None:
        raise ImportError(
            "TOML parsing requires Python 3.11+ or the 'tomli' package. "
            "Install with: pip install tomli"
        )

    with open(path, 'rb') as f:
        return tomllib.load(f)


def load_config(
    project_dir: Optional[Path] = None,
    include_global: bool = True,
    include_project: bool = True,
) -> GlobalConfig:
    """Load configuration from global and project config files.

    Project config takes precedence over global config.

    Args:
        project_dir: Directory to search for project config
        include_global: Whether to load global config
        include_project: Whether to load project config

    Returns:
        Merged GlobalConfig
    """
    config = GlobalConfig()

    # Load global config
    if include_global:
        global_path = get_global_config_path()
        if global_path.exists():
            try:
                global_data = parse_toml(global_path)
                config = GlobalConfig.from_dict(global_data)
            except Exception:
                pass  # Ignore errors in global config

    # Load project config (overrides global)
    if include_project:
        project_path = get_project_config_path(project_dir)
        if project_path:
            try:
                project_data = parse_toml(project_path)

                # Merge project config over global
                if 'defaults' in project_data:
                    for key, value in project_data['defaults'].items():
                        if hasattr(config.defaults, key):
                            setattr(config.defaults, key, value)

                if 'sharing' in project_data:
                    for key, value in project_data['sharing'].items():
                        if hasattr(config.sharing, key):
                            setattr(config.sharing, key, value)

                if 'paths' in project_data:
                    for key, value in project_data['paths'].items():
                        if hasattr(config.paths, key):
                            setattr(config.paths, key, value)

            except Exception:
                pass  # Ignore errors in project config

    return config


def create_default_config(path: Path) -> Path:
    """Create a default configuration file.

    Args:
        path: Path where to create the config file

    Returns:
        Path to created file
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    content = '''# termgif configuration file
# See https://github.com/example/termgif for documentation

[defaults]
# Default theme for terminal rendering
theme = "catppuccin"

# Default font size in pixels
font_size = 16

# GIF quality (1-5, higher is better but larger)
quality = 3

# Frames per second
fps = 10

# Default output format (gif, webp, mp4, webm, apng, svg)
format = "gif"

# Default terminal dimensions
width = 80
height = 24

# Padding around terminal in pixels
padding = 20

# Shell to use for live recording (empty = system default)
shell = ""

[sharing]
# Imgur API client ID for uploads
# Get one at: https://api.imgur.com/oauth2/addclient
imgur_client_id = ""

# Giphy API key for uploads
# Get one at: https://developers.giphy.com/
giphy_api_key = ""

# Default sharing service (catbox, imgur, giphy)
default_service = "catbox"

[paths]
# Custom templates directory
templates = ""

# Default output directory
output = ""
'''

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    return path


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a specific configuration value.

    Args:
        key: Dot-separated key (e.g., 'defaults.theme', 'sharing.imgur_client_id')
        default: Default value if not found

    Returns:
        Configuration value or default
    """
    config = load_config()

    parts = key.split('.')
    if len(parts) == 2:
        section, name = parts
        section_obj = getattr(config, section, None)
        if section_obj:
            return getattr(section_obj, name, default)

    return default


__all__ = [
    'GlobalConfig',
    'DefaultsConfig',
    'SharingConfig',
    'PathsConfig',
    'get_config_dir',
    'get_global_config_path',
    'get_project_config_path',
    'load_config',
    'create_default_config',
    'get_config_value',
]
