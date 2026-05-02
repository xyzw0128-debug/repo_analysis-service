from dataclasses import dataclass
from pathlib import Path
import fnmatch
import os

from core.logging import get_logger

logger = get_logger(__name__)

SKIP_DIRS = {'node_modules', 'vendor', '.git', 'dist', 'build', '__pycache__', '.cache', '.venv', 'venv'}
SKIP_PATTERNS = ['*.lock', '*.min.js', '*.min.css', '*.pyc', '*.pyo']
ALLOW_EXT = {'.py','.js','.ts','.jsx','.tsx','.go','.rs','.java','.rb','.php','.cs','.cpp','.c','.h','.yaml','.yml','.toml','.json','.md','.txt','.sh'}
ALLOW_NAMES = {'Dockerfile','docker-compose.yml','requirements.txt','package.json','Cargo.toml','go.mod','Makefile','.gitignore'}
SKIP_DIRS = {"node_modules", "vendor", ".git", "dist", "build", "__pycache__", ".cache", ".venv", "venv"}
SKIP_PATTERNS = ["*.lock", "*.min.js", "*.min.css", "*.pyc", "*.pyo"]
ALLOW_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".rb", ".php", ".cs", ".cpp", ".c", ".h", ".yaml", ".yml", ".toml", ".json", ".md", ".txt", ".sh"}
ALLOW_NAMES = {"Dockerfile", "docker-compose.yml", "requirements.txt", "package.json", "Cargo.toml", "go.mod", "Makefile", ".gitignore"}


@dataclass
class ScanResult:
    repo_tree: str
    selected_files: str


def detect_secrets(content: str) -> bool:
    markers = ['SECRET=', 'API_KEY=', 'PRIVATE KEY']
    return any(m in content for m in markers)


def _is_binary(path: Path) -> bool:
    with path.open('rb') as f:
        return b'\x00' in f.read(8000)


def scan_repository(clone_root: str) -> ScanResult:
    root = Path(clone_root)
    root_real = os.path.realpath(root)
    files = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            path = Path(dirpath) / fname
            rel = path.relative_to(root).as_posix()
            real = os.path.realpath(path)
            if not real.startswith(root_real):
                logger.warning('Path traversal blocked', extra={'path': rel})
                continue
            if path.is_symlink():
                continue
            if any(fnmatch.fnmatch(fname, pat) for pat in SKIP_PATTERNS):
                continue
            if path.stat().st_size > 100 * 1024:
                continue
            if path.suffix not in ALLOW_EXT and fname not in ALLOW_NAMES:
                continue
            if _is_binary(path):
                continue
            files.append(rel)
    files = sorted(files, key=_priority_key)

    repo_tree = '\n'.join(sorted(files))
    blocks = []
    total = 0
    selected = 0
    for rel in files:
        if selected >= 40:
            break
        path = root / rel
        content = path.read_text(errors='replace')
        b = len(content.encode())
        if total + b > 200 * 1024:
            break
        if detect_secrets(content):
            logger.warning('Secret detected; excluding content', extra={'path': rel})
            continue
        blocks.append(f'<<<FILE:{rel}>>>\n{content}\n<<<END_FILE>>>')
        total += b
        selected += 1
    return ScanResult(repo_tree=repo_tree, selected_files='\n\n'.join(blocks))


def _priority_key(rel: str):
    name = Path(rel).name
    lower = rel.lower()
    root_configs = {'requirements.txt','package.json','cargo.toml','go.mod','makefile','.gitignore'}
    if '/' not in rel and name.lower() in root_configs:
        return (0, rel)
    if name in {'Dockerfile', 'docker-compose.yml'} or lower.endswith('docker-compose.yml'):
        return (1, rel)
    if rel.startswith('.github/') or name == '.gitlab-ci.yml':
        return (2, rel)
    if rel.startswith(('src/','app/','lib/','core/','api/')):
        return (3, rel)
    if 'readme' in name.lower():
        return (4, rel)
    return (5, rel)
def _is_binary(path: Path) -> bool:
    with path.open("rb") as f:
        return b"\x00" in f.read(8000)


def _has_secrets(content: str) -> bool:
    needles = ["SECRET", "API_KEY", "PRIVATE KEY"]
    c = content.upper()
    return any(n in c for n in needles)


def _priority(rel: str) -> tuple:
    name = Path(rel).name
    if name in {"requirements.txt", "package.json", "Cargo.toml", "go.mod", "Makefile"}: return (1, rel)
    if name in {"Dockerfile", "docker-compose.yml"}: return (2, rel)
    if rel.startswith(".github/") or name == ".gitlab-ci.yml": return (3, rel)
    if rel.startswith(("src/", "app/", "lib/", "core/", "api/")): return (4, rel)
    if "readme" in name.lower(): return (5, rel)
    return (6, rel)


def scan_repository(clone_root: str, max_files: int = 40, max_total_bytes: int = 200 * 1024) -> ScanResult:
    root = Path(clone_root)
    root_real = os.path.realpath(root)
    files = []
    for p in root.rglob("*"):
        rel = p.relative_to(root).as_posix()
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.is_symlink() or not p.is_file():
            continue
        resolved = os.path.realpath(p)
        if not resolved.startswith(root_real):
            logger.warning("Path traversal blocked: %s", rel)
            continue
        if any(fnmatch.fnmatch(p.name, pat) for pat in SKIP_PATTERNS):
            continue
        if p.stat().st_size > 100 * 1024:
            continue
        if p.suffix not in ALLOW_EXTS and p.name not in ALLOW_NAMES:
            continue
        if _is_binary(p):
            continue
        files.append(rel)

    files.sort(key=_priority)
    repo_tree = "\n".join(files)
    blocks = []
    total = 0
    count = 0
    for rel in files:
        if count >= max_files or total >= max_total_bytes:
            break
        p = root / rel
        content = p.read_text(errors="ignore")
        b = len(content.encode())
        if total + b > max_total_bytes:
            continue
        if _has_secrets(content):
            logger.warning("Secrets detected; excluded: %s", rel)
            continue
        blocks.append(f"<<<FILE:{rel}>>>\n{content}\n<<<END_FILE>>>")
        total += b
        count += 1
    return ScanResult(repo_tree=repo_tree, selected_files="\n\n".join(blocks))
