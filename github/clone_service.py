import shutil
import subprocess
from pathlib import Path

from core.logging import get_logger

logger = get_logger(__name__)


class CloneError(Exception): ...


def clone_repository(job_id: str, repo_url: str, token: str, branch: str | None = None) -> Path:
    target = Path(f"/tmp/repoforge/{job_id}")
    if target.exists():
        shutil.rmtree(target, ignore_errors=True)
    auth_url = repo_url.replace("https://", f"https://x-access-token:{token}@")
    cmd = ["git", "clone", "--depth", "1"]
    if branch:
        cmd += ["--branch", branch]
    cmd += [auth_url, str(target)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Cloned repository %s", repo_url)
        return target
    except Exception as e:
        shutil.rmtree(target, ignore_errors=True)
        raise CloneError(str(e)) from e


def get_commit_sha(clone_path: str | Path) -> str:
    out = subprocess.check_output(["git", "-C", str(clone_path), "rev-parse", "HEAD"], text=True)
    return out.strip()


def cleanup(clone_path: str | Path):
    p = Path(clone_path)
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)
