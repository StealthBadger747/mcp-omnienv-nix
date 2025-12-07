import json
import os
import pytest

import mcp_omnienv_nix.server as server


def test_validate_packages_accepts_valid_names():
    assert server._validate_packages(["requests", "numpy"]) == ["requests", "numpy"]
    assert server._validate_packages(["requests", ""]) == ["requests"]


def test_validate_packages_rejects_invalid_names():
    with pytest.raises(ValueError):
        server._validate_packages(["bad name"])


def test_nix_shell_command_includes_base_and_extras():
    cmd = server._nix_shell_command("python", ["requests"], "echo ok")
    expr_index = cmd.index("--expr") + 1
    expr = cmd[expr_index]
    assert "python313.withPackages" in expr
    assert "ps.requests" in expr
    assert cmd[-2:] == ["-lc", "echo ok"]


def test_nix_shell_command_includes_each_language_base():
    # Ensure every supported language encodes the expected attr sets.
    cmd_py = server._nix_shell_command("python", [], "true")
    assert "python313.withPackages" in cmd_py[cmd_py.index("--expr") + 1]

    cmd_r = server._nix_shell_command("r", ["misty"], "true")
    expr_r = cmd_r[cmd_r.index("--expr") + 1]
    assert "pkgs.rWrapper.override" in expr_r
    assert "ps.misty" in expr_r

    cmd_ruby = server._nix_shell_command("ruby", ["rails"], "true")
    expr_rb = cmd_ruby[cmd_ruby.index("--expr") + 1]
    assert "pkgs.ruby_3_3" in expr_rb
    assert "ps.rails" in expr_rb

    cmd_lua = server._nix_shell_command("lua", ["luacheck"], "true")
    expr_lua = cmd_lua[cmd_lua.index("--expr") + 1]
    assert "pkgs.lua5_4.withPackages" in expr_lua
    assert "ps.luacheck" in expr_lua


def _run_and_assert(cmd: list[str]) -> None:
    result = server._run(cmd, timeout=180)
    if result["exit_code"] != 0:
        raise AssertionError(
            f"Command failed with {result['exit_code']}\nstdout:\n{result['stdout']}\nstderr:\n{result['stderr']}"
        )


def test_run_in_env_invokes_runner(monkeypatch):
    captured = {}

    def fake_run(cmd, timeout):
        captured["cmd"] = cmd
        captured["timeout"] = timeout
        return {"exit_code": 0, "stdout": "ok", "stderr": ""}

    monkeypatch.setattr(server, "_run", fake_run)
    result_json = server.run_in_env_impl("python", "echo ok", ["requests"], timeout_seconds=5)

    result = json.loads(result_json)
    assert result == {"exit_code": 0, "stdout": "ok", "stderr": ""}
    assert captured["timeout"] == 5
    # Ensure the constructed nix shell includes base and extras.
    joined_cmd = " ".join(captured["cmd"])
    assert "python313.withPackages" in joined_cmd
    assert "ps.requests" in joined_cmd


def test_run_in_env_rejects_unknown_language():
    with pytest.raises(ValueError):
        server.run_in_env_impl("go", "echo ok")


def _skip_if_no_integration():
    if not os.environ.get("MCP_OMNIENV_INTEGRATION"):
        pytest.skip("Set MCP_OMNIENV_INTEGRATION=1 to run integration tests that invoke nix shell")


@pytest.mark.integration
def test_integration_python_requests():
    _skip_if_no_integration()
    cmd = server._nix_shell_command("python", ["requests"], "python - <<'PY'\nimport requests\nprint('ok')\nPY")
    _run_and_assert(cmd)


@pytest.mark.integration
def test_integration_ruby_rake():
    _skip_if_no_integration()
    cmd = server._nix_shell_command("ruby", ["rake"], "ruby -e \"require 'rake'; puts 'ok'\"")
    _run_and_assert(cmd)


@pytest.mark.integration
def test_integration_r_jsonlite():
    _skip_if_no_integration()
    cmd = server._nix_shell_command("r", ["jsonlite"], "R -q -e \"library(jsonlite); cat('ok')\"")
    _run_and_assert(cmd)


@pytest.mark.integration
def test_integration_lua_luafilesystem():
    _skip_if_no_integration()
    cmd = server._nix_shell_command("lua", ["luafilesystem"], "lua -e \"require('lfs'); print('ok')\"")
    _run_and_assert(cmd)
