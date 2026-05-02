import shutil
import subprocess
from pathlib import Path


class CloneError(Exception):
    pass


def _auth_url(repo_url: str, token: str) -> str:
    return repo_url.replace('https://', f'https://x-access-token:{token}@')


def clone_repo(repo_url: str, branch: str, token: str, job_id: str) -> Path:
    clone_path = Path(f'/tmp/repoforge/{job_id}')
    if clone_path.exists():
        shutil.rmtree(clone_path, ignore_errors=True)
    clone_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(['git','clone','--depth','1','--branch',branch,_auth_url(repo_url, token), str(clone_path)], check=True, capture_output=True)
        return clone_path
    except Exception as exc:
        shutil.rmtree(clone_path, ignore_errors=True)
        raise CloneError(f'Clone failed for {repo_url}') from exc


def get_commit_sha(clone_path: str) -> str:
    result = subprocess.run(['git','-C',clone_path,'rev-parse','HEAD'], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def cleanup(clone_path: str) -> None:
    shutil.rmtree(clone_path, ignore_errors=True)
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
