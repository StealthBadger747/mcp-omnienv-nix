# mcp-omnienv-nix

MCP server that spins up Nix-backed, polyglot ephemeral environments. It uses `nix shell` to build disposable toolchains for interpreted stacks (Python, Node.js, Ruby, R, Lua; extendable) and runs your command inside that shell. Package availability depends on `nixpkgs` (e.g., `python313Packages.requests`, `rPackages.misty`, `nodePackages.sloc`).

## Why
- Coding agents often need ad-hoc Python/Node/Ruby/R/Lua deps. Preloading everything is noisy; venvs clutter a system.
- With Nix on the host, this server asks for packages on demand, pulls them into the store, and leaves the rest of the environment clean—no venvs or global installs.
- Runs over MCP (stdio transport) so agent clients can call the tools directly.

## Tools
- `list_languages` — enumerate supported languages and their base Nix packages.
- `run_in_env(language, command, extra_packages?, timeout_seconds?)` — launch a `nix shell` with base + extras and execute `command`. Returns JSON: `stdout`, `stderr`, `exit_code`.

## Quick start
```bash
# Try it ad-hoc
nix shell github:StealthBadger747/mcp-omnienv-nix -c mcp-omnienv-nix
```

Hook into your MCP client (stdio transport). Example config shape:
```json
{
  "mcpServers": {
    "mcp-omnienv-nix": {
      "command": "mcp-omnienv-nix"
    }
  }
}
```

## Extending languages
- Edit `SUPPORTED_LANGUAGES` in `mcp_omnienv_nix/server.py` to add a language and its base packages.
- `run_in_env` validates extra packages against a simple regex and appends them to the `nix shell` invocation.

## Development
```bash
# Nix dev shell with deps + pytest
nix develop . -c pytest
# Run integration tests (hit nix shell for real package resolution)
MCP_OMNIENV_INTEGRATION=1 nix develop . -c pytest -m integration
```

## License
MIT.
