"""Claude login from Telegram: runs `claude auth login` in a hidden tmux
session, sends you the link and types the code you paste back."""
import asyncio
import json
import re
import shlex
import subprocess
import time

from . import config, tmuxctl
from .i18n import t

SESSION = "pocket-login"  # must not start with tmuxctl.PREFIX
EXPIRES = 600
URL_RX = re.compile(r"https://\S+/oauth/authorize\S+")
CODE_RX = re.compile(r"^[^\s#]{8,}#[^\s#]{8,}$")
ERROR_RX = re.compile(r"error|invalid|failed|expired", re.I)

state = {"active": False, "since": 0.0}


def is_code(text):
    return bool(CODE_RX.match(text.strip()))


def _t():
    return f"={SESSION}:"


def _open():
    tmuxctl._tmux("kill-session", "-t", f"={SESSION}")
    cmd = f"{shlex.quote(config.get().claude_bin)} auth login"
    ok, err = tmuxctl.new_session(SESSION, None, cmd, width=400)
    if ok:
        tmuxctl._tmux("set-option", "-w", "-t", _t(), "remain-on-exit", "on")
    return ok, err


def cancel():
    state.update(active=False, since=0.0)
    tmuxctl._tmux("kill-session", "-t", f"={SESSION}")


def expired():
    if state["active"] and time.time() - state["since"] > EXPIRES:
        cancel()
        return True
    return False


def status():
    try:
        r = subprocess.run([config.get().claude_bin, "auth", "status"],
                           capture_output=True, text=True, timeout=30)
        d = json.loads(r.stdout)
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return False, t("login_status_failed")
    info = t("login_info", email=d.get("email", "?"), plan=d.get("subscriptionType", "?"))
    return bool(d.get("loggedIn")) and d.get("authMethod") == "claude.ai", info


def _dead():
    r = tmuxctl._tmux("display-message", "-p", "-t", _t(), "#{pane_dead}")
    return r.returncode != 0 or r.stdout.strip() == "1"


async def start():
    ok, err = await asyncio.to_thread(_open)
    if not ok:
        return None, t("login_open_failed", e=err)
    text = ""
    for _ in range(20):
        await asyncio.sleep(1)
        text = await asyncio.to_thread(tmuxctl.screen, SESSION)
        m = URL_RX.search(text)
        if m and "paste code" in text.lower():
            state.update(active=True, since=time.time())
            return m.group(0), None
    await asyncio.to_thread(cancel)
    return None, t("login_no_link", t=text[-1500:])


async def send_code(code):
    state["active"] = False
    await asyncio.to_thread(tmuxctl._tmux, "send-keys", "-t", _t(), "-l", code.strip())
    await asyncio.sleep(0.5)
    await asyncio.to_thread(tmuxctl._tmux, "send-keys", "-t", _t(), "Enter")
    finished = False
    for _ in range(30):
        await asyncio.sleep(1)
        if await asyncio.to_thread(_dead):
            finished = True
            break
    text = await asyncio.to_thread(tmuxctl.screen, SESSION)
    await asyncio.to_thread(cancel)
    ok, info = await asyncio.to_thread(status)
    if finished and ok and not ERROR_RX.search(text):
        return True, info
    return False, text[-1500:] or info
