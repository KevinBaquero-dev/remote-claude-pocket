"""Server status and the optional checks from config.toml."""
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from . import config
from .i18n import t


def uptime_seconds():
    return float(Path("/proc/uptime").read_text().split()[0])


def tailscale_ok():
    try:
        r = subprocess.run(["tailscale", "status", "--json"],
                           capture_output=True, text=True, timeout=10)
        return json.loads(r.stdout).get("BackendState") == "Running"
    except Exception:
        return False


def url_ok(url, retries=0):
    for i in range(retries + 1):
        try:
            if httpx.get(url, timeout=5).status_code < 400:
                return True
        except Exception:
            pass
        if i < retries:
            time.sleep(15)
    return False


def backup_age_hours():
    stamp = config.get().backup_stamp
    if not stamp:
        return None
    try:
        ts = datetime.fromisoformat(stamp.read_text().strip())
    except Exception:
        try:
            ts = datetime.fromtimestamp(stamp.stat().st_mtime, timezone.utc)
        except Exception:
            return None
    if ts.tzinfo is None:
        ts = ts.astimezone()
    return (datetime.now(timezone.utc) - ts).total_seconds() / 3600


def run_checks():
    """{name: (ok, detail)} for every enabled check."""
    s = config.get()
    res = {}
    if s.tailscale:
        res["Tailscale"] = (tailscale_ok(), "")
    for c in s.checks:
        res[c.name] = (url_ok(c.url, retries=2), "")
    if s.backup_stamp:
        age = backup_age_hours()
        res["Backup"] = (age is not None and age <= s.backup_max_hours,
                         t("st_backup_none") if age is None
                         else t("st_backup_age", h=age))
    return res


async def ping():
    url = config.get().hc_ping_url
    if not url:
        return
    try:
        async with httpx.AsyncClient() as c:
            await c.get(url, timeout=10)
    except Exception:
        pass


async def pause_check():
    """Pauses the Healthchecks.io check before a planned shutdown."""
    s = config.get()
    if not s.hc_ping_url or not s.hc_api_key:
        return None
    uuid = s.hc_ping_url.rstrip("/").rsplit("/", 1)[-1]
    try:
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"https://healthchecks.io/api/v3/checks/{uuid}/pause",
                headers={"X-Api-Key": s.hc_api_key}, timeout=10)
        return r.status_code == 200
    except httpx.HTTPError:
        return False


def _meminfo():
    m = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        k, v = line.split(":", 1)
        m[k] = int(v.split()[0])
    return m


def _temp():
    temps = []
    for z in Path("/sys/class/thermal").glob("thermal_zone*"):
        try:
            kind = (z / "type").read_text().strip()
            v = int((z / "temp").read_text()) / 1000
            if kind == "x86_pkg_temp":
                return v
            temps.append(v)
        except Exception:
            pass
    return max(temps) if temps else None


def duration(sec):
    d, r = divmod(int(sec), 86400)
    h, r = divmod(r, 3600)
    return (f"{d} d " if d else "") + f"{h} h {r // 60} min"


def status_text(n_sessions):
    s = config.get()
    m = _meminfo()
    gb = lambda kb: kb / 1048576
    du = shutil.disk_usage("/")
    temp = _temp()
    up, down = t("st_up"), t("st_down")
    lines = [
        t("st_uptime", v=duration(uptime_seconds())),
        t("st_cpu", l=os.getloadavg()[0], n=os.cpu_count()),
        t("st_ram", u=gb(m["MemTotal"] - m["MemAvailable"]), t=gb(m["MemTotal"])),
        t("st_swap", u=gb(m["SwapTotal"] - m["SwapFree"]), t=gb(m["SwapTotal"])),
        t("st_disk", u=du.used / 1e9, t=du.total / 1e9, p=du.used * 100 // du.total),
        t("st_temp", v=temp) if temp is not None else t("st_temp_none"),
        t("st_sessions", n=n_sessions),
    ]
    if s.tailscale:
        lines.append(f"Tailscale: {up if tailscale_ok() else down}")
    for c in s.checks:
        lines.append(f"{c.name}: {up if url_ok(c.url) else down}")
    if s.backup_stamp:
        age = backup_age_hours()
        if age is None:
            v = t("st_backup_none")
        else:
            v = t("st_backup_age", h=age) + (t("st_alert") if age > s.backup_max_hours else "")
        lines.append(t("st_backup", v=v))
    lines.append(t("st_reboot", v=t("yes") if Path("/var/run/reboot-required").exists()
                   else t("no")))
    return "\n".join(lines)
