# Remote Claude Pocket

[Español](README.es.md)

Run Claude Code on your own server and drive it from your phone through Telegram.

You type `open myapp` and the bot starts Claude Code in that project inside tmux, with remote control turned on. The session then shows up in the Claude app (claude.ai/code, iOS or Android) and you keep working from there. The bot also watches your sessions and messages you when one of them needs you.

It's built for one person with one server (a home box, a VPS, an old laptop) who works remotely and often from a phone.

## What it does

- **Opens and closes sessions:** `open myapp`, `close myapp`, `close all`. Names can be partial and you can set aliases (`alias app = my-long-app-name`).
- **Shows a session's screen:** `show myapp` sends you the terminal as text.
- **Warns you when a session is stuck:** login required, usage limit reached, API error, waiting for you to pick an option, or no activity for 24 hours.
- **Logs Claude in from Telegram:** `login` sends you the OAuth link, you paste the code back, and the bot deletes your message.
- **Server status:** `status` shows uptime, CPU, RAM, disk, temperature and your own checks (HTTP endpoints, Tailscale, backup age), with alerts when a check fails.
- **Optional reboot and shutdown** (`reboot server`, `shutdown server`), always with a confirmation button.
- **English and Spanish:** replies in the language you choose, and commands work in both.

Sessions run in their own systemd scope, so restarting or updating the bot never kills them.

## Requirements

- Linux with systemd (user services) and tmux
- Python 3.11 or newer
- [Claude Code](https://docs.claude.com/en/docs/claude-code), logged in at least once
- A Telegram bot token from [@BotFather](https://t.me/BotFather) and your numeric user id (from [@userinfobot](https://t.me/userinfobot))

## Install

```bash
git clone https://github.com/KevinBaquero-dev/remote-claude-pocket.git ~/remote-claude-pocket
cd ~/remote-claude-pocket
./install.sh
```

Then:

1. Put `TELEGRAM_TOKEN` and `ALLOWED_USER_ID` in `~/.config/remote-claude-pocket/.env`.
2. Review `~/.config/remote-claude-pocket/config.toml`. Set `projects_dir` to the folder that holds your projects, and `language`.
3. Start it with `systemctl --user enable --now remote-claude-pocket`.
4. Keep it running after you log out with `loginctl enable-linger $USER`.

Open your bot in Telegram and send `/start` (Telegram doesn't let a bot message you first). Logs: `journalctl --user -u remote-claude-pocket -f`.

## Configuration

Every option is commented in [`config.example.toml`](config.example.toml):

| Option | Default | What it does |
| --- | --- | --- |
| `language` | `"en"` | `"en"` or `"es"` |
| `projects_dir` | `~/projects` | Each subfolder is a project |
| `hidden_projects` | `[]` | Subfolders the bot never lists |
| `remote_control` | `true` | Start sessions with `--remote-control` |
| `skip_permissions` | `false` | Start with `--dangerously-skip-permissions` |
| `auto_trust` | `true` | Accept the folder-trust prompt |
| `power_commands` | `false` | Allow reboot and shutdown |
| `inactivity_hours` | `24` | Idle warning (`0` turns it off) |
| `tailscale`, `[[checks]]`, `backup_stamp` | off | Health checks |

Secrets go only in `.env`, which `install.sh` creates with mode 600. Optional extras there: `HC_PING_URL` and `HC_API_KEY` for [Healthchecks.io](https://healthchecks.io).

### Reboot and shutdown

`power_commands = true` also needs permission for your user to run `systemctl reboot` and `systemctl poweroff`. Use the polkit rule in [`extras/`](extras/50-remote-claude-pocket-power.rules): replace `USERNAME` and copy it to `/etc/polkit-1/rules.d/`.

## Security

Read this before you install it:

- **Only your user id is obeyed.** Commands, messages and buttons from anyone else are ignored. Anyone who has the bot token can still run a bot with it, so treat the token like a password. The bot warns you if another instance starts using it.
- **What you see goes through Telegram.** Commands like `show` send terminal output to Telegram's servers. Don't use the bot for code or data that can't leave your machine.
- **`skip_permissions` is off by default.** Turning it on means Claude runs any command without asking, and you're usually not watching. Turn it on only in projects you'd let it touch freely.
- **Nothing listens on the network.** The bot polls Telegram over an outgoing connection, so you don't open any ports.

## Development

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
```

## License

[MIT](LICENSE)
