"""Reads Claude's screen and reports sessions that are stuck (login,
usage limit, API error, waiting on a choice) or idle for too long."""
import hashlib
import re
import time

LAST_LINES = 15

RULES = [
    ("login", re.compile(
        r"please run /login|invalid api key|oauth token (has )?expired"
        r"|not logged in", re.I)),
    ("limit", re.compile(
        r"limit reached|(hit|reached) your [\w\s-]{0,30}limit", re.I)),
    ("error", re.compile(r"^\s*⎿?\s*API Error")),
    ("dialog", re.compile(r"^\s*❯\s*\d+\.\s+\S")),
]

_mem = {}


def classify(screen):
    lines = [l for l in screen.splitlines() if l.strip()][-LAST_LINES:]
    for state, rx in RULES:
        for line in lines:
            if rx.search(line):
                return state, line.strip()
    return "normal", ""


def check(name, screen, idle_seconds, now=None):
    """New events: ("state", state, line) or ("idle", hours)."""
    now = time.time() if now is None else now
    h = hashlib.md5(screen.encode()).hexdigest()
    m = _mem.setdefault(name, {"state": "normal", "hash": h,
                               "changed": now, "warned": False})
    events = []
    if h != m["hash"]:
        m.update(hash=h, changed=now, warned=False)
    state, line = classify(screen)
    if state != m["state"]:
        m["state"] = state
        if state != "normal":
            events.append(("state", state, line))
    if idle_seconds > 0 and not m["warned"] and now - m["changed"] >= idle_seconds:
        m["warned"] = True
        events.append(("idle", int((now - m["changed"]) // 3600)))
    return events


def keep(name):
    if name in _mem:
        _mem[name].update(changed=time.time(), warned=False)


def forget_missing(names):
    for n in list(_mem):
        if n not in names:
            del _mem[n]


TRUST_RX = re.compile(r"accessing workspace|trust (the files in )?this folder", re.I)
YES_OPTION_RX = re.compile(r"^\s*❯?\s*(\d+)\.\s+Yes\b", re.I)


def trust_downs(screen):
    """If the folder-trust prompt is on screen, how many Down presses reach
    the "Yes" option (the cursor starts on option 1). None otherwise."""
    if not TRUST_RX.search(screen):
        return None
    for line in screen.splitlines():
        m = YES_OPTION_RX.match(line)
        if m:
            return int(m.group(1)) - 1
    return None
