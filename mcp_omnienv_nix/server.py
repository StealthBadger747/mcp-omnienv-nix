#!/usr/bin/env python3
"""mcp-omnienv-nix: MCP server for Nix-backed polyglot ephemeral envs."""

from __future__ import annotations

import json
import re
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
    # Interpreted runtimes where we can build an env via withPackages.
    "python": LanguageProfile(label="Python 3.13", base_packages=["python313"]),
    "ruby": LanguageProfile(label="Ruby 3.3", base_packages=["ruby_3_3"]),
    "r": LanguageProfile(label="R", base_packages=["R"]),
    "lua": LanguageProfile(label="Lua 5.4", base_packages=["lua5_4"]),
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
    # Import nixpkgs via flake to avoid relying on NIX_PATH.
    pkgs_expr = 'import (builtins.getFlake "nixpkgs") {}'

    if lang == "python":
        extra_expr = " ".join([f"ps.{p}" for p in packages])
        expr = (
            f"let pkgs = {pkgs_expr}; in pkgs.{profile.base_packages[0]}.withPackages (ps: [ {extra_expr} ])"
        )
    elif lang == "ruby":
        extras = " ".join([f"ps.{p}" for p in packages])
        expr = f"let pkgs = {pkgs_expr}; in pkgs.{profile.base_packages[0]}.withPackages (ps: [ {extras} ])"
    elif lang == "r":
        extras = " ".join([f"ps.{p}" for p in packages])
        expr = f"let pkgs = {pkgs_expr}; in pkgs.rWrapper.override {{ packages = ps: [ {extras} ]; }}"
    elif lang == "lua":
        extras = " ".join([f"ps.{p}" for p in packages])
        expr = f"let pkgs = {pkgs_expr}; in pkgs.lua5_4.withPackages (ps: [ {extras} ])"
    else:
        # Should not happen because of the guard above.
        raise ValueError(f"Unsupported language '{lang}'")

    return [
        "nix",
        "shell",
        "--extra-experimental-features",
        "nix-command flakes",
        "--impure",
        "--expr",
        expr,
        "--command",
        "bash",
        "-lc",
        command,
    ]


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


def run_in_env_impl(
    language: str, command: str, extra_packages: list[str] | None = None, timeout_seconds: int = 120
) -> str:
    """Run a shell command in a disposable Nix shell for the chosen language."""
    extras = _validate_packages(extra_packages or [])
    cmd = _nix_shell_command(language.lower(), extras, command)
    result = _run(cmd, timeout=timeout_seconds)
    return json.dumps(result, indent=2)


# Expose as MCP tool while keeping a plain callable for tests and reuse.
run_in_env = mcp.tool()(run_in_env_impl)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
