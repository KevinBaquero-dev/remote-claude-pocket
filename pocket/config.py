"""Settings: secrets from .env, everything else from config.toml.

Both live in $POCKET_CONFIG_DIR (default ~/.config/remote-claude-pocket).
Nothing is read at import time, so tests can import every module freely.
"""
import os
import shutil
import tomllib
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


def config_dir():
    return Path(os.environ.get("POCKET_CONFIG_DIR",
                               Path.home() / ".config/remote-claude-pocket"))


def state_dir():
    return Path(os.environ.get("POCKET_STATE_DIR",
                               Path.home() / ".local/state/remote-claude-pocket"))


@dataclass
class Check:
    name: str
    url: str


@dataclass
class Settings:
    token: str = ""
    allowed_user_id: int | None = None
    hc_ping_url: str = ""
    hc_api_key: str = ""

    language: str = "en"
    projects_dir: Path = field(default_factory=lambda: Path.home() / "projects")
    hidden_projects: set[str] = field(default_factory=set)
    claude_bin: str = "claude"
    remote_control: bool = True
    skip_permissions: bool = False
    auto_trust: bool = True
    power_commands: bool = False
    inactivity_hours: int = 24
    tailscale: bool = False
    checks: list[Check] = field(default_factory=list)
    backup_stamp: Path | None = None
    backup_max_hours: int = 36


def _load_env(path):
    vals = {}
    if not path.exists():
        return vals
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


def _path(v):
    return Path(os.path.expanduser(v)) if v else None


def _claude_bin(v):
    if v:
        return os.path.expanduser(v)
    found = shutil.which("claude")
    if found:
        return found
    return str(Path.home() / ".local/bin/claude")


def load(directory=None):
    directory = Path(directory) if directory else config_dir()
    env = _load_env(directory / ".env")
    toml_path = directory / "config.toml"
    t = tomllib.loads(toml_path.read_text()) if toml_path.exists() else {}

    try:
        uid = int(env.get("ALLOWED_USER_ID", ""))
    except ValueError:
        uid = None

    lang = str(t.get("language", "en")).lower()
    s = Settings(
        token=env.get("TELEGRAM_TOKEN", ""),
        allowed_user_id=uid,
        hc_ping_url=env.get("HC_PING_URL", ""),
        hc_api_key=env.get("HC_API_KEY", ""),
        language=lang if lang in ("en", "es") else "en",
        projects_dir=_path(t.get("projects_dir")) or Path.home() / "projects",
        hidden_projects=set(t.get("hidden_projects", [])),
        claude_bin=_claude_bin(t.get("claude_bin", "")),
        remote_control=bool(t.get("remote_control", True)),
        skip_permissions=bool(t.get("skip_permissions", False)),
        auto_trust=bool(t.get("auto_trust", True)),
        power_commands=bool(t.get("power_commands", False)),
        inactivity_hours=int(t.get("inactivity_hours", 24)),
        tailscale=bool(t.get("tailscale", False)),
        checks=[Check(str(c["name"]), str(c["url"]))
                for c in t.get("checks", [])],
        backup_stamp=_path(t.get("backup_stamp", "")),
        backup_max_hours=int(t.get("backup_max_hours", 36)),
    )
    return s


@lru_cache(maxsize=1)
def get():
    return load()
