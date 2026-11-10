import re
import string

import pytest

from pocket import commands, config, i18n, monitor, sessions, store, tmuxctl


@pytest.fixture(autouse=True)
def aislado(tmp_path, monkeypatch):
    monkeypatch.setenv("POCKET_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setenv("POCKET_STATE_DIR", str(tmp_path / "state"))
    (tmp_path / "cfg").mkdir()
    config.get.cache_clear()
    yield tmp_path
    config.get.cache_clear()
    i18n.LANG = "en"


@pytest.mark.parametrize("text,action,arg", [
    ("open myapp", "open", "myapp"),
    ("Abre Claude en acme", "open", "acme"),
    ("open claude in my-app", "open", "my-app"),
    ("abrir", "open", ""),
    ("close all", "close_all", ""),
    ("cierra todas las sesiones", "close_all", ""),
    ("close myapp", "close", "myapp"),
    ("cierra Claude en app", "close", "app"),
    ("muéstrame", None, ""),
    ("show", "show", ""),
    ("muestra app", "show", "app"),
    ("Sesiones", "sessions", ""),
    ("status", "status", ""),
    ("estado", "status", ""),
    ("alias app = my-long-app", "alias", "app = my-long-app"),
    ("aliases", "aliases", ""),
    ("remove alias app", "remove_alias", "app"),
    ("borra alias app", "remove_alias", "app"),
    ("reboot server", "reboot", ""),
    ("reinicia el servidor", "reboot", ""),
    ("shut down the server", "shutdown", ""),
    ("apaga servidor", "shutdown", ""),
    ("login", "login", ""),
    ("inicia sesión", "login", ""),
    ("cancel login", "cancel_login", ""),
    ("cancela el login", "cancel_login", ""),
    ("ayuda", "help", ""),
    ("whatever", None, ""),
])
def test_parse_both_languages(text, action, arg):
    assert commands.parse(text) == (action, arg)


def test_menu_buttons_parse():
    for lang in ("en", "es"):
        i18n.LANG = lang
        assert [commands.parse(b)[0] for b in i18n.t("menu")] == [
            "open", "sessions", "status"]


def test_every_text_has_both_languages_with_same_fields():
    fields = lambda s: {f for _, f, _, _ in string.Formatter().parse(s) if f}
    for key, entry in i18n.TEXTS.items():
        assert set(entry) == {"en", "es"}, key
        if isinstance(entry["en"], str):
            assert fields(entry["en"]) == fields(entry["es"]), key


def test_config_defaults_are_safe(aislado):
    s = config.get()
    assert s.skip_permissions is False
    assert s.power_commands is False
    assert s.language == "en"
    assert s.token == "" and s.allowed_user_id is None


def test_config_file(aislado):
    d = aislado / "cfg"
    (d / ".env").write_text('TELEGRAM_TOKEN="abc"\nALLOWED_USER_ID=42\n')
    (d / "config.toml").write_text(
        'language = "es"\nprojects_dir = "~/code"\nhidden_projects = ["x"]\n'
        'skip_permissions = true\n[[checks]]\nname = "web"\nurl = "http://127.0.0.1:1"\n')
    s = config.get()
    assert (s.token, s.allowed_user_id, s.language) == ("abc", 42, "es")
    assert s.projects_dir.name == "code" and s.hidden_projects == {"x"}
    assert s.skip_permissions and s.checks[0].name == "web"


def test_claude_command_flags(aislado):
    (aislado / "cfg/config.toml").write_text('claude_bin = "/bin/claude"\n')
    assert tmuxctl.claude_command("my app") == "/bin/claude --remote-control 'my app'"
    (aislado / "cfg/config.toml").write_text(
        'claude_bin = "/bin/claude"\nskip_permissions = true\nremote_control = false\n')
    config.get.cache_clear()
    assert tmuxctl.claude_command("x") == "/bin/claude --dangerously-skip-permissions"


def test_session_name():
    assert tmuxctl.session_name("my app.v2") == "rcp-my-app-v2"
    from pocket import login
    assert not login.SESSION.startswith(tmuxctl.PREFIX)


def test_projects_resolve_with_alias_and_hidden(aislado):
    root = aislado / "p"
    for n in ("acme-core", "acme-web", "secret", ".git"):
        (root / n).mkdir(parents=True)
    (aislado / "cfg/config.toml").write_text(
        f'projects_dir = "{root}"\nhidden_projects = ["secret"]\n')
    assert sessions.projects() == ["acme-core", "acme-web"]
    assert sessions.resolve("acm") == ["acme-core", "acme-web"]
    assert sessions.resolve("ACME-WEB") == ["acme-web"]
    store.set_alias("Ac", "acme-core")
    assert sessions.resolve("ac") == ["acme-core"]
    assert store.remove_alias("ac") and not store.remove_alias("ac")


def test_monitor_states_and_idle():
    assert monitor.classify("hola\nPlease run /login")[0] == "login"
    assert monitor.classify("You've hit your weekly limit")[0] == "limit"
    assert monitor.classify("  ⎿  API Error: 500")[0] == "error"
    assert monitor.classify("❯ 1. Yes\n  2. No")[0] == "dialog"
    assert monitor.classify("all good")[0] == "normal"
    monitor._mem.clear()
    assert monitor.check("s", "a", 3600, now=0) == []
    assert monitor.check("s", "Please run /login", 3600, now=10)[0][:2] == ("state", "login")
    assert monitor.check("s", "Please run /login", 3600, now=3700) == [("idle", 1)]
    assert monitor.check("s", "Please run /login", 3600, now=9000) == []
    assert monitor.check("t", "x", 0, now=0) == []
    assert monitor.check("t", "x", 0, now=10 ** 6) == []


def test_trust_prompt():
    bypass = ("Accessing workspace:\n /home/u/p\n"
              "❯ 1. No, exit\n  2. Yes, I accept")
    trust = ("Do you trust the files in this folder?\n"
             "❯ 1. Yes, proceed\n  2. No, exit")
    assert monitor.trust_downs(bypass) == 1
    assert monitor.trust_downs(trust) == 0
    assert monitor.trust_downs("❯ 1. Yes") is None


def test_no_personal_data_in_sources():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    bad = re.compile(r"/home/\w+")
    for f in list(root.glob("pocket/*.py")) + list(root.glob("*.md")) + \
            list(root.glob("*.toml*")) + list(root.glob("systemd/*")) + list(root.glob("extras/*")):
        assert not bad.search(f.read_text()), f
