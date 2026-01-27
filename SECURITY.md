# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in termgif, please report it responsibly:

1. **DO NOT** open a public GitHub issue for security vulnerabilities
2. Email the maintainers directly or use GitHub's private vulnerability reporting
3. Include as much detail as possible:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to understand and address the issue.

## Security Considerations

### Recording Modes

termgif has three recording modes with different security implications:

| Mode | Flag | Commands Executed | Risk Level |
|------|------|-------------------|------------|
| **Live** | (default) | Yes | Higher - runs real commands |
| **Simulate** | `--simulate` | No | Safe - typing animation only |
| **Terminal** | `--terminal` | Yes | Higher - captures screen |

### Recommendations

1. **Use `--simulate` for untrusted scripts**
   ```bash
   # Safe - doesn't execute any commands
   termgif untrusted_script.tg --simulate
   ```

2. **Review scripts before running in live mode**
   - Scripts can execute arbitrary shell commands
   - Commands run with your user permissions
   - Check for dangerous commands like `rm -rf`, `curl | sh`, etc.

3. **Be careful with `require` directive**
   - Only checks if command exists, doesn't validate safety
   - Scripts may still contain malicious commands

4. **Uploaded GIFs may contain sensitive information**
   - Terminal recordings may capture:
     - Usernames and hostnames (visible in prompt)
     - File paths and directory structures
     - Command outputs with sensitive data
   - Review recordings before sharing publicly

### API Keys

If using Imgur or Giphy upload features:

1. Store API keys in the config file (not in scripts)
2. Config file location:
   - Linux/macOS: `~/.config/termgif/config.toml`
   - Windows: `%APPDATA%\termgif\config.toml`
3. Ensure config file has appropriate permissions (readable only by you)

### Dependencies

termgif uses these external dependencies:

- **PIL/Pillow** - Image processing
- **typer** - CLI framework
- **rich** - Terminal output
- **requests** (optional) - For upload features
- **watchdog** (optional) - For watch mode
- **ffmpeg** (optional, external) - For video output

Keep dependencies updated to get security patches:
```bash
pip install --upgrade termgif
```

## Known Limitations

1. **No sandboxing**: Commands run with full user permissions
2. **No input validation**: Scripts can contain any shell commands
3. **Screen capture**: Terminal mode may capture sensitive on-screen data

## Changelog

Security-related changes are noted in release notes with the `[Security]` tag.
