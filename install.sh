#!/usr/bin/env bash
# Installs Remote Claude Pocket for the current user. No sudo needed.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CFG="${POCKET_CONFIG_DIR:-$HOME/.config/remote-claude-pocket}"
UNIT_DIR="$HOME/.config/systemd/user"
PY="${PYTHON:-python3}"

need() { command -v "$1" >/dev/null || { echo "Missing: $1"; exit 1; }; }
need "$PY"; need tmux; need systemctl
"$PY" -c 'import sys; sys.exit(sys.version_info < (3, 11))' \
  || { echo "Python 3.11+ required"; exit 1; }
command -v claude >/dev/null || [ -x "$HOME/.local/bin/claude" ] \
  || echo "Warning: claude not found. Install Claude Code first."

echo "> Virtualenv"
"$PY" -m venv "$DIR/.venv"
"$DIR/.venv/bin/pip" install -q --upgrade pip
"$DIR/.venv/bin/pip" install -q -r "$DIR/requirements.txt"

echo "> Config in $CFG"
mkdir -p "$CFG"
[ -f "$CFG/config.toml" ] || cp "$DIR/config.example.toml" "$CFG/config.toml"
if [ ! -f "$CFG/.env" ]; then
  (umask 077; cp "$DIR/.env.example" "$CFG/.env")
fi
chmod 600 "$CFG/.env"

echo "> systemd user service"
mkdir -p "$UNIT_DIR"
sed "s#%h/remote-claude-pocket#$DIR#g" "$DIR/systemd/remote-claude-pocket.service" \
  > "$UNIT_DIR/remote-claude-pocket.service"
systemctl --user daemon-reload

cat <<MSG

Done. Next:
  1. Put your bot token and Telegram user id in $CFG/.env
  2. Review $CFG/config.toml (projects_dir, language...)
  3. systemctl --user enable --now remote-claude-pocket
  4. To keep it running after you log out: loginctl enable-linger $USER
Logs: journalctl --user -u remote-claude-pocket -f
MSG
