from pathlib import Path
from github.file_scanner import scan_repository


def test_symlink_skipped(tmp_path: Path):
    (tmp_path / 'a.py').write_text('print(1)')
    (tmp_path / 'b.py').symlink_to(tmp_path / 'a.py')
    out = scan_repository(str(tmp_path))
    assert 'b.py' not in out.repo_tree


def test_binary_and_large_and_non_allowlisted_skipped(tmp_path: Path):
    (tmp_path / 'bin.py').write_bytes(b'\x00abc')
    (tmp_path / 'big.py').write_text('a' * (101 * 1024))
    (tmp_path / 'x.exe').write_text('hello')
    out = scan_repository(str(tmp_path))
    assert 'bin.py' not in out.repo_tree
    assert 'big.py' not in out.repo_tree
    assert 'x.exe' not in out.repo_tree


def test_priority_order_and_secret_excluded(tmp_path: Path):
    (tmp_path / 'src').mkdir()
    (tmp_path / 'src' / 'z.py').write_text('print(1)')
    (tmp_path / 'README.md').write_text('readme')
    (tmp_path / 'requirements.txt').write_text('flask')
    (tmp_path / 'secret.py').write_text('API_KEY=abc')
    out = scan_repository(str(tmp_path))
    lines = out.repo_tree.splitlines()
    assert 'secret.py' in lines
    assert '<<<FILE:secret.py>>>' not in out.selected_files
    assert lines.index('requirements.txt') < lines.index('src/z.py')


def test_path_traversal_blocked_and_logged(tmp_path: Path, monkeypatch, caplog):
    p = tmp_path / 'a.py'
    p.write_text('print(1)')
    import github.file_scanner as fs
    realpath = fs.os.path.realpath

    def fake_realpath(arg):
        if str(arg).endswith('a.py'):
            return '/outside/a.py'
        return realpath(arg)

    monkeypatch.setattr(fs.os.path, 'realpath', fake_realpath)
    out = fs.scan_repository(str(tmp_path))
    assert 'a.py' not in out.repo_tree
    assert any('Path traversal blocked' in rec.message for rec in caplog.records)
