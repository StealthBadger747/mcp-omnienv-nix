# mcp-omnienv-nix

MCP server that spins up Nix-backed, polyglot ephemeral environments. Call `run_in_env` to run a shell command inside a temporary Nix shell for Python, Node.js, Ruby, or R (more can be added). The server exposes:

- `list_languages`: enumerate supported languages and base Nix packages.
- `run_in_env(language, command, extra_packages?, timeout_seconds?)`: launch a `nix shell` with base + extra packages and execute the command; returns JSON with `stdout`, `stderr`, and `exit_code`.

CLI entrypoint: `mcp-omnienv-nix`.
