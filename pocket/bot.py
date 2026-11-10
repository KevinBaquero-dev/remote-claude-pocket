"""Telegram bot: handlers, buttons and background jobs."""
import asyncio
import html
import logging
import re
import socket
import time
from datetime import datetime

from telegram import (BotCommand, InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, Update)
from telegram.constants import ParseMode
from telegram.error import BadRequest, Conflict, NetworkError, TimedOut
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          MessageHandler, filters)

from . import config, health, i18n, login, monitor, sessions, store, tmuxctl
from .commands import SLASH, norm, parse
from .i18n import t
from .sessions import project_of

log = logging.getLogger("remote-claude-pocket")

RC_TEXTS = ("/rc active", "remote-control is active")
STARTUP_WAIT = 30
CLOSING = set()
CONFLICTS = []
esc = html.escape


def cfg():
    return config.get()


def menu():
    return ReplyKeyboardMarkup([t("menu")], resize_keyboard=True, is_persistent=True)


def pre(text, limit=3500):
    lines = [l.rstrip() for l in text.splitlines() if l.strip()]
    s = re.sub(r"─{20,}", "─" * 20, "\n".join(lines))[-limit:]
    return f"<pre>{esc(s) or t('empty_screen')}</pre>"


def bold(name):
    return f"<b>{esc(project_of(name))}</b>"


def session_buttons(name):
    return [InlineKeyboardButton(t("btn_show"), callback_data=f"show:{name}"),
            InlineKeyboardButton(t("btn_close"), callback_data=f"close:{name}")]


def confirm(yes_key, data):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t(yes_key), callback_data=data),
        InlineKeyboardButton(t("btn_no"), callback_data=data.split(":")[0] + ":no")]])


async def edit(msg, text, keyboard=None):
    try:
        await msg.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    except BadRequest as e:
        if "not modified" not in str(e).lower():
            raise


async def open_project(msg, project):
    store.mark_opened(project)
    name = tmuxctl.session_name(project)
    b = f"<b>{esc(project)}</b>"
    if tmuxctl.exists(name):
        await edit(msg, t("already_open", b=b), InlineKeyboardMarkup([session_buttons(name)]))
        return
    await edit(msg, t("opening", b=b))
    ok, err = await asyncio.to_thread(
        tmuxctl.open_claude, name, cfg().projects_dir / project, project)
    if not ok:
        await edit(msg, t("open_failed", b=b, err=pre(err)))
        return
    sessions.register(name, project)
    if cfg().remote_control:
        await edit(msg, t("enabling_rc", b=b))
    trusted = not cfg().auto_trust
    p = ""
    for i in range(STARTUP_WAIT):
        await asyncio.sleep(1)
        if not tmuxctl.exists(name):
            sessions.unregister(name)
            await edit(msg, t("died_on_start", b=b, p=pre(p)))
            return
        p = tmuxctl.screen(name)
        if cfg().remote_control and any(x in p.lower() for x in RC_TEXTS):
            await edit(msg, t("ready_rc", b=b), InlineKeyboardMarkup([session_buttons(name)]))
            return
        downs = None if trusted else monitor.trust_downs(p)
        if downs is not None:
            trusted = True
            await edit(msg, t("trusting", b=b))
            for _ in range(downs):
                tmuxctl.keys(name, "Down")
                await asyncio.sleep(0.2)
            tmuxctl.keys(name, "Enter")
        if not cfg().remote_control and i >= 4 and "❯" in p:
            await edit(msg, t("ready_plain", b=b), InlineKeyboardMarkup([session_buttons(name)]))
            return
    key = "no_rc" if cfg().remote_control else "ready_plain"
    await edit(msg, t(key, b=b, s=STARTUP_WAIT, p=pre(p)),
               InlineKeyboardMarkup([session_buttons(name)]))


async def close(name):
    if not tmuxctl.exists(name):
        sessions.unregister(name)
        return t("already_closed")
    CLOSING.add(name)
    try:
        await asyncio.to_thread(tmuxctl.type_text, name, "/exit")
        for _ in range(15):
            await asyncio.sleep(1)
            if not tmuxctl.exists(name):
                return t("closed")
        tmuxctl.kill(name)
        return t("force_closed")
    finally:
        sessions.unregister(name)
        CLOSING.discard(name)


async def close_one(msg, name):
    await edit(msg, t("closing", b=bold(name)))
    r = await close(name)
    await edit(msg, f"{bold(name)}: {r}.")


async def close_everything():
    names = [s["name"] for s in tmuxctl.list_sessions()]
    res = await asyncio.gather(*(close(n) for n in names))
    return [f"{bold(n)}: {r}" for n, r in zip(names, res)]


async def close_all(msg):
    n = len(tmuxctl.list_sessions())
    if not n:
        await edit(msg, t("no_sessions"))
        return
    await edit(msg, t("closing_n", n=n))
    await edit(msg, "\n".join(await close_everything()))


async def power(msg, order):
    if not cfg().power_commands:
        await edit(msg, t("power_disabled"))
        return
    await edit(msg, t("preparing"))
    n = len(tmuxctl.list_sessions())
    lines = []
    if n:
        await edit(msg, t("closing_n", n=n))
        lines = await close_everything()
    if order == "shutdown":
        paused = await health.pause_check()
        if paused is not None:
            lines.append(t("hc_paused") if paused else t("hc_not_paused"))
        final, cmd = t("shutting_down"), "poweroff"
    else:
        final, cmd = t("rebooting"), "reboot"
    await edit(msg, "\n".join(lines + [final]))
    p = await asyncio.create_subprocess_exec(
        "systemctl", cmd, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT)
    out, _ = await p.communicate()
    if p.returncode != 0:
        error = esc(out.decode(errors="replace").strip()[-500:])
        await edit(msg, "\n".join(lines + [t("power_failed", cmd=cmd),
                                           f"<pre>{error}</pre>"]))


async def show(message, name):
    if not tmuxctl.exists(name):
        await message.reply_text(t("session_gone"))
        return
    await message.reply_text(
        f"{bold(name)}\n{pre(tmuxctl.screen(name))}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([session_buttons(name)]))


def sessions_text():
    d, _, _ = sessions.reconcile()
    if not d:
        return t("no_sessions"), None
    lines, rows = [], []
    for n, info in sorted(d.items(), key=lambda x: x[1]["opened"]):
        p = info["project"]
        since = health.duration(time.time() - info["opened"])
        lines.append(t("open_since", p=f"<b>{esc(p)}</b>", t=since))
        rows.append([
            InlineKeyboardButton(t("btn_show_p", p=p), callback_data=f"show:{n}"),
            InlineKeyboardButton(t("btn_close_p", p=p), callback_data=f"close:{n}")])
    if len(d) > 1:
        rows.append([InlineKeyboardButton(t("btn_close_all"), callback_data="all:ask")])
    return "\n".join(lines), InlineKeyboardMarkup(rows)


async def run(message, action, p):
    if action == "help":
        power_help = t("help_power") if cfg().power_commands else ""
        await message.reply_text(t("help", power=power_help),
                                 parse_mode=ParseMode.HTML, reply_markup=menu())
    elif action == "open":
        options = sessions.resolve(p) if p else sessions.projects()
        if not options:
            await message.reply_text(t("not_found", p=p, dir=cfg().projects_dir))
        elif len(options) == 1 and p:
            msg = await message.reply_text(t("opening_short"))
            await open_project(msg, options[0])
        else:
            rows = [[InlineKeyboardButton(o, callback_data=f"open:{o}")] for o in options]
            await message.reply_text(t("which_project"),
                                     reply_markup=InlineKeyboardMarkup(rows))
    elif action in ("close", "show"):
        options = (sessions.matching_open(p) if p
                   else [s["name"] for s in tmuxctl.list_sessions()])
        if not options:
            await message.reply_text(t("no_sessions_match", p=p) if p else t("no_sessions"))
        elif len(options) == 1:
            if action == "close":
                msg = await message.reply_text(t("closing_short"))
                await close_one(msg, options[0])
            else:
                await show(message, options[0])
        else:
            rows = [[InlineKeyboardButton(project_of(n), callback_data=f"{action}:{n}")]
                    for n in options]
            await message.reply_text(t("which_session"),
                                     reply_markup=InlineKeyboardMarkup(rows))
    elif action == "close_all":
        await message.reply_text(t("confirm_close_all"),
                                 reply_markup=confirm("btn_yes_close_all", "all:yes"))
    elif action == "sessions":
        text, kb = sessions_text()
        await message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    elif action == "status":
        n = len(tmuxctl.list_sessions())
        await message.reply_text(await asyncio.to_thread(health.status_text, n))
    elif action == "alias":
        a, _, target = p.partition("=")
        a, target = a.strip(), target.strip()
        if not re.fullmatch(r"[a-z0-9_-]+", a):
            await message.reply_text(t("alias_invalid"))
            return
        options = sessions.resolve(target)
        if len(options) != 1:
            await message.reply_text(t("alias_ambiguous", d=target,
                                       l=", ".join(options) or t("none")))
            return
        store.set_alias(a, options[0])
        await message.reply_text(t("alias_set", a=a, p=options[0]))
    elif action == "aliases":
        al = store.aliases()
        await message.reply_text("\n".join(f"{a} = {d}" for a, d in sorted(al.items()))
                                 if al else t("no_aliases"))
    elif action == "remove_alias":
        key = "alias_removed" if store.remove_alias(p) else "alias_missing"
        await message.reply_text(t(key, a=p))
    elif action in ("reboot", "shutdown"):
        if not cfg().power_commands:
            await message.reply_text(t("power_disabled"))
        elif action == "reboot":
            await message.reply_text(t("confirm_reboot"),
                                     reply_markup=confirm("btn_yes_reboot", "power:reboot"))
        else:
            await message.reply_text(t("confirm_shutdown"),
                                     reply_markup=confirm("btn_yes_shutdown", "power:shutdown"))
    elif action == "login":
        msg = await message.reply_text(t("login_starting"))
        await login_flow(msg)
    elif action == "cancel_login":
        await asyncio.to_thread(login.cancel)
        await message.reply_text(t("login_cancelled"))


async def on_text(update, context):
    raw = update.message.text.strip()
    if login.state["active"] and login.is_code(raw):
        await receive_code(update.message, raw)
        return
    action, p = parse(raw)
    if action:
        await run(update.message, action, p)
    else:
        await update.message.reply_text(t("not_understood"), reply_markup=menu())


async def on_command(update, context):
    cmd = update.message.text.split()[0][1:].split("@")[0].lower()
    await run(update.message, SLASH[cmd], norm(" ".join(context.args)))


async def on_button(update, context):
    q = update.callback_query
    if q.from_user.id != cfg().allowed_user_id:
        return
    await q.answer()
    action, _, arg = q.data.partition(":")
    msg = q.message
    if action == "open" and arg in sessions.projects():
        await open_project(msg, arg)
    elif action == "close":
        await close_one(msg, arg)
    elif action == "show":
        await show(msg, arg)
    elif action == "keep":
        monitor.keep(arg)
        await edit(msg, t("kept", b=bold(arg)))
    elif action == "login":
        await login_flow(await msg.reply_text(t("login_starting")))
    elif action == "all":
        if arg == "ask":
            await msg.reply_text(t("confirm_close_all"),
                                 reply_markup=confirm("btn_yes_close_all", "all:yes"))
        elif arg == "yes":
            await close_all(msg)
        else:
            await edit(msg, t("cancelled"))
    elif action == "power":
        if arg not in ("reboot", "shutdown"):
            await edit(msg, t("cancelled"))
        elif time.time() - msg.date.timestamp() > 300:
            await edit(msg, t("confirm_expired"))
        else:
            await power(msg, arg)


async def notify(context, text, keyboard=None):
    await context.bot.send_message(cfg().allowed_user_id, text,
                                   parse_mode=ParseMode.HTML, reply_markup=keyboard)


def login_button():
    return [[InlineKeyboardButton(t("btn_login"), callback_data="login:start")]]


async def login_flow(msg):
    url, err = await login.start()
    if not url:
        await edit(msg, f"<pre>{esc(err[-1500:])}</pre>")
        return
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_login_link"), url=url)]])
    await edit(msg, t("login_instructions"), kb)


async def receive_code(message, code):
    try:
        await message.delete()
    except Exception:
        pass
    msg = await message.chat.send_message(t("code_received"))
    ok, info = await login.send_code(code)
    if ok:
        await edit(msg, t("login_done", i=esc(info)))
    else:
        await edit(msg, t("login_failed", i=f"<pre>{esc(info)}</pre>"),
                   InlineKeyboardMarkup(login_button()))


WHY = {"login": "why_login", "limit": "why_limit",
       "error": "why_error", "dialog": "why_dialog"}


async def job_monitor(context):
    found = tmuxctl.list_sessions()
    monitor.forget_missing({s["name"] for s in found})
    if login.expired():
        await notify(context, t("login_expired"))
    now = time.time()
    idle = cfg().inactivity_hours * 3600
    for s in found:
        n = s["name"]
        if n in CLOSING or not s["alive"] or now - s["created"] < 90:
            continue
        text = await asyncio.to_thread(tmuxctl.screen, n)
        for ev in monitor.check(n, text, idle, now):
            if ev[0] == "state":
                _, state, line = ev
                rows = [session_buttons(n)] + (login_button() if state == "login" else [])
                await notify(context,
                             f"{bold(n)}: {t(WHY[state])}\n<code>{esc(line[:300])}</code>",
                             InlineKeyboardMarkup(rows))
            else:
                kb = InlineKeyboardMarkup([[
                    InlineKeyboardButton(t("btn_close"), callback_data=f"close:{n}"),
                    InlineKeyboardButton(t("btn_keep"), callback_data=f"keep:{n}")]])
                await notify(context, t("idle", b=bold(n), h=ev[1]), kb)


async def job_ping(context):
    await health.ping()


async def job_health(context):
    res = await asyncio.to_thread(health.run_checks)
    prev = context.bot_data.setdefault("health", {})
    for name, (ok, det) in res.items():
        before = prev.get(name, True)
        extra = f" ({esc(det)})" if det else ""
        if before and not ok:
            await notify(context, t("check_down", n=esc(name), d=extra))
        elif not before and ok:
            await notify(context, t("check_up", n=esc(name), d=extra))
        prev[name] = ok


async def job_cleanup(context):
    _, vanished, dead = sessions.reconcile()
    for n in vanished + dead:
        if n not in CLOSING:
            await notify(context, t("session_cleaned", p=esc(project_of(n))))


async def on_error(update, context):
    if isinstance(context.error, (NetworkError, TimedOut)):
        log.warning("Network: %s", context.error)
        return
    uid = cfg().allowed_user_id
    if isinstance(context.error, Conflict):
        now = time.time()
        CONFLICTS[:] = [x for x in CONFLICTS if now - x < 600] + [now]
        log.warning("Conflict (%d in 10 min): %s", len(CONFLICTS), context.error)
        if len(CONFLICTS) == 4:
            try:
                await context.bot.send_message(uid, t("conflict"))
            except Exception:
                pass
        return
    log.error("Error", exc_info=context.error)
    try:
        await context.bot.send_message(uid, t("bot_error", e=str(context.error)[:500]))
    except Exception:
        pass


async def post_init(app):
    await app.bot.set_my_commands([
        BotCommand("open", t("cmd_open")),
        BotCommand("sessions", t("cmd_sessions")),
        BotCommand("status", t("cmd_status")),
        BotCommand("closeall", t("cmd_closeall")),
        BotCommand("help", t("cmd_help")),
    ])
    d, _, _ = sessions.reconcile()
    now = datetime.now().strftime("%H:%M")
    if health.uptime_seconds() < 600:
        text = t("server_online", host=esc(socket.gethostname()), t=now)
    else:
        text = t("bot_restarted", t=now)
    if d:
        text += "\n" + t("open_count", n=len(d))
    try:
        await app.bot.send_message(cfg().allowed_user_id, text, reply_markup=menu())
    except BadRequest as e:
        # Telegram won't let a bot message you until you send it /start.
        log.warning("Could not message user %s (%s). Send /start to the bot.",
                    cfg().allowed_user_id, e)
    jq = app.job_queue
    if cfg().hc_ping_url:
        jq.run_repeating(job_ping, 300, first=5)
    if cfg().tailscale or cfg().checks or cfg().backup_stamp:
        jq.run_repeating(job_health, 300, first=60)
    jq.run_repeating(job_cleanup, 600, first=600)
    jq.run_repeating(job_monitor, 120, first=120)


def build(settings):
    me = filters.User(user_id=settings.allowed_user_id)
    app = (Application.builder().token(settings.token).concurrent_updates(True)
           .post_init(post_init).build())
    app.add_handler(CommandHandler(list(SLASH), on_command, filters=me))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(me & filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(on_error)
    return app


def main():
    logging.basicConfig(format="%(levelname)s %(name)s: %(message)s", level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    s = config.get()
    if not s.token or s.allowed_user_id is None:
        raise SystemExit(f"Missing TELEGRAM_TOKEN or ALLOWED_USER_ID in "
                         f"{config.config_dir() / '.env'}")
    i18n.LANG = s.language
    build(s).run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
