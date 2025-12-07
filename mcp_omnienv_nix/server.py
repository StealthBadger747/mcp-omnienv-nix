#!/usr/bin/env python3
"""mcp-omnienv-nix: MCP server for Nix-backed polyglot ephemeral envs."""

from __future__ import annotations

import json
import re
import shlex
import subprocess
from dataclasses import dataclass
from typing import Iterable, List

from fastmcp import FastMCP


mcp = FastMCP("mcp-omnienv-nix")


@dataclass(frozen=True)
class LanguageProfile:
    label: str
    base_packages: List[str]


SUPPORTED_LANGUAGES: dict[str, LanguageProfile] = {
    "python": LanguageProfile(label="Python 3.12", base_packages=["python312"]),
    "node": LanguageProfile(label="Node.js 22", base_packages=["nodejs_22"]),
    "ruby": LanguageProfile(label="Ruby 3.3", base_packages=["ruby_3_3"]),
    "r": LanguageProfile(label="R", base_packages=["R"]),
}

_PACKAGE_RE = re.compile(r"^[a-zA-Z0-9+_.-]+$")


def _validate_packages(pkgs: Iterable[str]) -> list[str]:
    validated: list[str] = []
    for pkg in pkgs:
        pkg = pkg.strip()
        if not pkg:
            continue
        if not _PACKAGE_RE.match(pkg):
            raise ValueError(f"Invalid package name: {pkg}")
        validated.append(pkg)
    return validated


def _nix_shell_command(lang: str, packages: list[str], command: str) -> list[str]:
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language '{lang}'. Supported: {', '.join(SUPPORTED_LANGUAGES)}")

    profile = SUPPORTED_LANGUAGES[lang]
    pkg_specs = [f"nixpkgs#{p}" for p in profile.base_packages + packages]

    # Construct: nix shell pkg1 pkg2 --command bash -lc "<command>"
    return ["nix", "shell", *pkg_specs, "--command", "bash", "-lc", command]


def _run(cmd: list[str], timeout: int = 120) -> dict[str, str | int]:
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )
    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


@mcp.tool()
def list_languages() -> str:
    """List supported languages and their base Nix packages."""
    lines = []
    for key, profile in SUPPORTED_LANGUAGES.items():
        base = ", ".join(profile.base_packages)
        lines.append(f"- {key}: {profile.label} (base: {base})")
    return "\n".join(lines)


@mcp.tool()
def run_in_env(language: str, command: str, extra_packages: list[str] | None = None, timeout_seconds: int = 120) -> str:
    """Run a shell command in a disposable Nix shell for the chosen language."""
    extras = _validate_packages(extra_packages or [])
    cmd = _nix_shell_command(language.lower(), extras, command)
    result = _run(cmd, timeout=timeout_seconds)
    return json.dumps(result, indent=2)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
