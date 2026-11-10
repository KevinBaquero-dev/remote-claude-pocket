# Remote Claude Pocket

[English](README.md)

Corre Claude Code en tu propio servidor y manéjalo desde el celular por Telegram.

Escribes `abre miapp` y el bot arranca Claude Code en ese proyecto dentro de tmux, con el control remoto activado. La sesión aparece en la app de Claude (claude.ai/code, iOS o Android) y sigues trabajando desde ahí. El bot además vigila tus sesiones y te escribe cuando alguna te necesita.

Está pensado para una persona con un servidor (un equipo en casa, un VPS, un portátil viejo) que trabaja remoto y muchas veces desde el celular.

## Qué hace

- **Abre y cierra sesiones:** `abre miapp`, `cierra miapp`, `cierra todas`. Los nombres pueden ir incompletos y puedes crear alias (`alias app = mi-app-de-nombre-largo`).
- **Muestra la pantalla de una sesión:** `muestra miapp` te manda la terminal como texto.
- **Te avisa cuando una sesión se traba:** pide login, llegó al límite de uso, muestra un error de la API, espera que elijas una opción o lleva 24 horas sin actividad.
- **Hace el login de Claude desde Telegram:** `login` te manda el link de OAuth, pegas el código y el bot borra tu mensaje.
- **Estado del servidor:** `estado` muestra tiempo encendido, CPU, RAM, disco, temperatura y tus propios chequeos (URLs, Tailscale, edad del backup), con alertas cuando alguno falla.
- **Reinicio y apagado opcionales** (`reinicia servidor`, `apaga servidor`), siempre con botón de confirmación.
- **Español e inglés:** responde en el idioma que elijas y entiende los comandos en los dos.

Las sesiones corren en su propio scope de systemd, así que reiniciar o actualizar el bot nunca las mata.

## Requisitos

- Linux con systemd (servicios de usuario) y tmux
- Python 3.11 o más nuevo
- [Claude Code](https://docs.claude.com/en/docs/claude-code), con login hecho al menos una vez
- Un token de bot de Telegram de [@BotFather](https://t.me/BotFather) y tu id numérico de usuario (de [@userinfobot](https://t.me/userinfobot))

## Instalación

```bash
git clone https://github.com/KevinBaquero-dev/remote-claude-pocket.git ~/remote-claude-pocket
cd ~/remote-claude-pocket
./install.sh
```

Después:

1. Pon `TELEGRAM_TOKEN` y `ALLOWED_USER_ID` en `~/.config/remote-claude-pocket/.env`.
2. Revisa `~/.config/remote-claude-pocket/config.toml`. Pon en `projects_dir` la carpeta donde están tus proyectos y en `language`, `"es"`.
3. Arráncalo con `systemctl --user enable --now remote-claude-pocket`.
4. Para que siga corriendo cuando cierres sesión: `loginctl enable-linger $USER`.

Escríbele `ayuda` a tu bot. Logs: `journalctl --user -u remote-claude-pocket -f`.

## Configuración

Todas las opciones están comentadas en [`config.example.toml`](config.example.toml):

| Opción | Por defecto | Qué hace |
| --- | --- | --- |
| `language` | `"en"` | `"en"` o `"es"` |
| `projects_dir` | `~/projects` | Cada subcarpeta es un proyecto |
| `hidden_projects` | `[]` | Subcarpetas que el bot nunca muestra |
| `remote_control` | `true` | Arranca las sesiones con `--remote-control` |
| `skip_permissions` | `false` | Arranca con `--dangerously-skip-permissions` |
| `auto_trust` | `true` | Acepta la pregunta de confianza de carpeta |
| `power_commands` | `false` | Permite reiniciar y apagar |
| `inactivity_hours` | `24` | Aviso de inactividad (`0` lo apaga) |
| `tailscale`, `[[checks]]`, `backup_stamp` | apagados | Chequeos de salud |

Los secretos van solo en `.env`, que `install.sh` crea con permisos 600. Ahí también puedes poner `HC_PING_URL` y `HC_API_KEY` si usas [Healthchecks.io](https://healthchecks.io).

### Reinicio y apagado

`power_commands = true` necesita además que tu usuario pueda correr `systemctl reboot` y `systemctl poweroff`. Usa la regla de polkit de [`extras/`](extras/50-remote-claude-pocket-power.rules): cambia `USERNAME` y cópiala a `/etc/polkit-1/rules.d/`.

## Seguridad

Léelo antes de instalarlo:

- **Solo obedece a tu id de usuario.** Ignora comandos, mensajes y botones de cualquier otra persona. Aun así, cualquiera con el token puede correr un bot con él, así que cuídalo como una contraseña. El bot te avisa si otra instancia empieza a usarlo.
- **Lo que ves pasa por Telegram.** Comandos como `muestra` mandan la salida de la terminal a los servidores de Telegram. No uses el bot con código o datos que no puedan salir de tu equipo.
- **`skip_permissions` viene apagado.** Si lo prendes, Claude corre cualquier comando sin preguntar, y casi nunca vas a estar mirando. Préndelo solo en proyectos donde lo dejarías hacer lo que quiera.
- **No escucha en la red.** El bot consulta a Telegram con una conexión de salida, así que no abres ningún puerto.

## Desarrollo

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
```

## Licencia

[MIT](LICENSE)
