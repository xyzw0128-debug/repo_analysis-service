from pathlib import Path
import os

from github.file_scanner import scan_repository


def test_symlink_binary_large_and_non_allowlist_skipped(tmp_path: Path):
    (tmp_path / "a.py").write_text("print(1)")
    (tmp_path / "b.bin").write_bytes(b"\x00\x01")
    (tmp_path / "c.xyz").write_text("x")
    (tmp_path / "big.py").write_text("a" * (101 * 1024))
    os.symlink(tmp_path / "a.py", tmp_path / "link.py")
    r = scan_repository(str(tmp_path))
    assert "a.py" in r.repo_tree
    assert "b.bin" not in r.repo_tree
    assert "c.xyz" not in r.repo_tree
    assert "big.py" not in r.repo_tree
    assert "link.py" not in r.repo_tree


def test_path_traversal_blocked_and_logged(tmp_path: Path, monkeypatch, caplog):
    f = tmp_path / "a.py"; f.write_text("print(1)")
    monkeypatch.setattr("os.path.realpath", lambda p: "/etc/passwd" if str(p).endswith("a.py") else str(tmp_path))
    scan_repository(str(tmp_path))
    assert "Path traversal blocked" in caplog.text


def test_priority_and_secret(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text("flask")
    (tmp_path / "Dockerfile").write_text("FROM python")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("print(1)")
    (tmp_path / "README.md").write_text("readme")
    (tmp_path / "secret.py").write_text("API_KEY=abc")
    r = scan_repository(str(tmp_path))
    lines = r.repo_tree.splitlines()
    assert lines[0] == "requirements.txt"
    assert lines[1] == "Dockerfile"
    assert "secret.py" in r.repo_tree
    assert "<<<FILE:secret.py>>>" not in r.selected_files
