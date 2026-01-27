"""Built-in templates for common workflows."""
from pathlib import Path
from typing import Dict

# Template registry
_TEMPLATES: Dict[str, str] = {}


def register_template(name: str, content: str) -> None:
    """Register a template.

    Args:
        name: Template name
        content: Template content
    """
    _TEMPLATES[name.lower()] = content


def get_template(name: str) -> str:
    """Get a template by name.

    Args:
        name: Template name

    Returns:
        Template content

    Raises:
        ValueError: If template not found
    """
    name = name.lower()
    if name not in _TEMPLATES:
        available = ", ".join(sorted(_TEMPLATES.keys()))
        raise ValueError(f"Unknown template '{name}'. Available: {available}")
    return _TEMPLATES[name]


def list_templates() -> list[str]:
    """Get list of available template names.

    Returns:
        Sorted list of template names
    """
    return sorted(_TEMPLATES.keys())


def render_template(template_name: str, **kwargs) -> str:
    """Get a template and format it with provided variables.

    Args:
        template_name: Template name
        **kwargs: Variables to substitute (name, title, etc.)

    Returns:
        Formatted template content
    """
    template = get_template(template_name)

    # Default values
    defaults = {
        "name": "demo",
        "title": "Demo",
    }
    defaults.update(kwargs)

    return template.format(**defaults)


# ============================================================================
# Built-in Templates
# ============================================================================

register_template("basic", '''// {name}.tg - termgif recording script
// Run: termgif {name}

@output "{name}.gif"
@title "{title}"
@theme "mocha"

// Your commands here
-> "echo Hello, World!" >>
~1s

-> "ls -la" >>
~2s
''')

register_template("git", '''// {name}.tg - Git workflow demo
// Run: termgif {name}

@output "{name}.gif"
@title "Git Workflow"
@theme "mocha"
@size 100x24

// Check status
-> "git status" >>
~1s

// Stage changes
-> "git add ." >>
~500ms

// Commit
-> "git commit -m \\"Update\\"" >>
~1s

// View log
-> "git log --oneline -5" >>
~2s

// Push changes
-> "git push" >>
~2s
''')

register_template("npm", '''// {name}.tg - npm workflow demo
// Run: termgif {name}

@output "{name}.gif"
@title "npm Workflow"
@theme "dracula"
@size 100x24

// Initialize project
-> "npm init -y" >>
~1s

// Install dependencies
-> "npm install express" >>
~3s

// List packages
-> "npm list" >>
~1s

// Run scripts
-> "npm run dev" >>
~2s
''')

register_template("docker", '''// {name}.tg - Docker workflow demo
// Run: termgif {name}

@output "{name}.gif"
@title "Docker Demo"
@theme "nord"
@size 100x24

// List containers
-> "docker ps" >>
~1s

// List images
-> "docker images" >>
~1s

// Build image
-> "docker build -t myapp ." >>
~3s

// Run container
-> "docker run -d -p 8080:80 myapp" >>
~1s

// Check running containers
-> "docker ps" >>
~2s
''')

register_template("python", '''// {name}.tg - Python REPL demo
// Run: termgif {name}

@output "{name}.gif"
@title "Python Demo"
@theme "gruvbox"
@size 80x24

// Start Python
-> "python3" >>
~500ms

// Simple calculation
-> "2 + 2" >>
~500ms

// Define a function
-> "def greet(name):" >>
-> "    return f'Hello, {{name}}!'" >>
~500ms

-> "" >>
~300ms

// Call the function
-> "greet('World')" >>
~1s

// Exit
-> "exit()" >>
~500ms
''')

register_template("vim", '''// {name}.tg - Vim demo
// Run: termgif {name} --native
// Or:  termgif {name} --terminal

@output "{name}.gif"
@title "Vim Demo"
@theme "tokyo"
@native

// Start vim
-> "vim hello.txt" >>
~1s

// Enter insert mode
key "i"

// Type some text
-> "Hello from Vim!"
~500ms

// Exit insert mode
key "escape"

// Save and quit
-> ":wq" >>
~1s
''')

register_template("htop", '''// {name}.tg - htop demo
// Run: termgif {name} --native

@output "{name}.gif"
@title "htop Demo"
@theme "mocha"
@native
@size 120x30

// Start htop
-> "htop" >>
~2s

// Sort by CPU
key "F6"
~500ms
key "down"
key "down"
key "enter"
~2s

// Quit
key "q"
~500ms
''')

register_template("fzf", '''// {name}.tg - fzf demo
// Run: termgif {name} --terminal

@output "{name}.gif"
@title "fzf Demo"
@theme "dracula"

// Find files with fzf
-> "ls | fzf" >>
~1s

// Type to filter
-> "main"
~500ms

// Navigate
key "down"
key "down"

// Select
key "enter"
~1s
''')

register_template("lazygit", '''// {name}.tg - lazygit demo
// Run: termgif {name} --native

@output "{name}.gif"
@title "lazygit Demo"
@theme "tokyo"
@native
@size 120x30

// Start lazygit
-> "lazygit" >>
~2s

// Navigate
key "j"
key "j"
~500ms

// View details
key "enter"
~1s

// Quit
key "q"
~500ms
''')

register_template("api", '''// {name}.tg - API testing demo
// Run: termgif {name}

@output "{name}.gif"
@title "API Testing"
@theme "material"
@size 100x24

// GET request
-> "curl -s https://api.github.com/users/octocat | jq '.login, .name'" >>
~2s

// POST request with data
-> "curl -X POST -H \\"Content-Type: application/json\\" -d '{{\"key\":\"value\"}}' https://httpbin.org/post | jq '.json'" >>
~2s
''')
