"""Projects on disk and the registry of open Claude sessions."""
import time

from . import config, store, tmuxctl
from .commands import norm

REGISTRY = "sessions.json"


def projects():
    s = config.get()
    if not s.projects_dir.is_dir():
        return []
    names = [p.name for p in s.projects_dir.iterdir()
             if p.is_dir() and not p.name.startswith(".")
             and p.name not in s.hidden_projects]
    rec = store.recent()
    return sorted(names, key=lambda n: (-rec.get(n, 0), n.lower()))


def resolve(text):
    """Projects matching text: alias, exact name, or substring."""
    t = norm(text)
    names = projects()
    target = store.aliases().get(t)
    if target in names:
        return [target]
    exact = [n for n in names if norm(n) == t]
    if exact:
        return exact
    return [n for n in names if t in norm(n)]


def project_of(name):
    return name[len(tmuxctl.PREFIX):]


def matching_open(text):
    """Open sessions matching text (alias, exact or substring)."""
    names = [s["name"] for s in tmuxctl.list_sessions()]
    t = norm(store.aliases().get(norm(text), text))
    exact = [n for n in names if norm(project_of(n)) == t]
    return exact or [n for n in names if t in norm(project_of(n))]


def register(name, project):
    d = store.read(REGISTRY)
    d[name] = {"project": project, "opened": int(time.time())}
    store.write(REGISTRY, d)


def unregister(name):
    d = store.read(REGISTRY)
    d.pop(name, None)
    store.write(REGISTRY, d)


def reconcile():
    """Syncs the registry with tmux. Returns (registry, vanished, dead)."""
    real = {s["name"]: s for s in tmuxctl.list_sessions()}
    d = store.read(REGISTRY)
    vanished = [n for n in list(d) if n not in real]
    for n in vanished:
        d.pop(n)
    dead = []
    for n, s in real.items():
        if not s["alive"]:
            tmuxctl.kill(n)
            d.pop(n, None)
            dead.append(n)
        elif n not in d:
            d[n] = {"project": project_of(n), "opened": s["created"]}
    store.write(REGISTRY, d)
    return d, vanished, dead
