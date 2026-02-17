import importlib
from pathlib import Path


def load_module(monkeypatch, tmp_path):
    monkeypatch.setenv("REPOS_ROOT", str(tmp_path / "repos"))
    import services.proxy.git_proxy as git_proxy
    return importlib.reload(git_proxy)


def test_whitelist_mutation_reflects_validation_and_status(monkeypatch, tmp_path):
    gp = load_module(monkeypatch, tmp_path)

    # Initial default whitelist blocks custom host
    ok, _ = gp.validate_git_url("https://git.example.com/org/repo")
    assert not ok

    added, _ = gp.add_to_whitelist("git.example.com")
    assert added

    # Validation should immediately reflect updated whitelist
    ok, msg = gp.validate_git_url("https://git.example.com/org/repo")
    assert ok, msg

    status = __import__("asyncio").run(gp.status())
    assert "git.example.com" in status["allowed_hosts"]

    removed, _ = gp.remove_from_whitelist("git.example.com")
    assert removed

    ok, _ = gp.validate_git_url("https://git.example.com/org/repo")
    assert not ok


def test_clone_depth_is_forced_to_one(monkeypatch, tmp_path):
    gp = load_module(monkeypatch, tmp_path)

    commands = []

    class Result:
        returncode = 0
        stderr = ""

    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        target = Path(cmd[-1])
        target.mkdir(parents=True, exist_ok=True)
        (target / "README.md").write_text("ok")
        return Result()

    monkeypatch.setattr(gp.subprocess, "run", fake_run)

    success, _ = gp.git_clone("https://github.com/org/repo", "repo1", depth=999)
    assert success

    assert commands, "Expected subprocess.run to be called"
    cmd = commands[0]
    assert cmd[0:3] == ["git", "clone", "--depth"]
    assert cmd[3] == "1"
    assert gp.clone_log[-1]["requested_depth"] == 999
    assert gp.clone_log[-1]["effective_depth"] == 1


def test_host_validation_rejects_malformed_host_tricks(monkeypatch, tmp_path):
    gp = load_module(monkeypatch, tmp_path)

    bad_urls = [
        "https://github.com.:443/org/repo",  # trailing dot + explicit port
        "https://github.com@evil.com/org/repo",  # userinfo host confusion
        "https://github.com/org//repo",  # malformed path
        "https://github.com/org/repo?ref=main",  # query
        "https://github.com/org/repo#frag",  # fragment
    ]

    for url in bad_urls:
        ok, _ = gp.validate_git_url(url)
        assert not ok, f"Expected URL to be rejected: {url}"
