"""Thin wrapper over tmux. Each Claude session lives in a tmux session
named rcp-<project>, started in its own systemd scope so restarting the
bot never kills the sessions."""
import shlex
import shutil
import subprocess
import time

from . import config

PREFIX = "rcp-"


def _tmux(*args):
    return subprocess.run(["tmux", *args], capture_output=True, text=True)


def session_name(project):
    clean = "".join(c if c.isalnum() or c in "-_" else "-" for c in project)
    return PREFIX + clean


def _t(name):
    return f"={name}:"


def exists(name):
    return _tmux("has-session", "-t", f"={name}").returncode == 0


def claude_command(title):
    s = config.get()
    parts = [shlex.quote(s.claude_bin)]
    if s.skip_permissions:
        parts.append("--dangerously-skip-permissions")
    if s.remote_control:
        parts += ["--remote-control", shlex.quote(title)]
    return " ".join(parts)


def new_session(name, cwd, command, width=200):
    tmux = ["tmux", "new-session", "-d", "-s", name,
            "-x", str(width), "-y", "50"]
    if cwd:
        tmux += ["-c", str(cwd)]
    tmux.append(command)
    if shutil.which("systemd-run"):
        tmux = ["systemd-run", "--user", "--scope", "--quiet", *tmux]
    r = subprocess.run(tmux, capture_output=True, text=True)
    return r.returncode == 0, r.stderr.strip()


def open_claude(name, path, title):
    return new_session(name, path, claude_command(title))


def screen(name):
    r = _tmux("capture-pane", "-p", "-J", "-t", _t(name))
    return r.stdout.rstrip() if r.returncode == 0 else ""


def keys(name, *k):
    return _tmux("send-keys", "-t", _t(name), *k).returncode == 0


def type_text(name, text):
    ok = _tmux("send-keys", "-t", _t(name), "-l", text).returncode == 0
    time.sleep(0.3)
    return ok and keys(name, "Enter")


def kill(name):
    return _tmux("kill-session", "-t", f"={name}").returncode == 0


def list_sessions():
    fmt = "#{session_name}\t#{session_created}\t#{pane_dead}\t#{pane_pid}"
    r = _tmux("list-sessions", "-F", fmt)
    if r.returncode != 0:
        return []
    out = []
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 4 or not parts[0].startswith(PREFIX):
            continue
        name, created, dead, pid = parts
        out.append({
            "name": name,
            "created": int(created) if created.isdigit() else 0,
            "alive": dead == "0",
            "pid": int(pid) if pid.isdigit() else 0,
        })
    return out
