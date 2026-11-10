"""Bot texts in English and Spanish. Commands are understood in both
languages regardless of this setting; it only picks the replies."""

LANG = "en"

TEXTS = {
    "help": {
        "en": (
            "<b>Remote Claude Pocket</b>\n\n"
            "open myapp\n"
            "open  (no name: lists your projects)\n"
            "close myapp\n"
            "close all\n"
            "sessions\n"
            "show myapp\n"
            "alias app = my-long-app-name\n"
            "aliases\n"
            "remove alias app\n"
            "status\n"
            "login\n"
            "{power}"
            "\nNames can be partial: app finds my-long-app-name.\n"
            "Spanish works too: abre, cierra, muestra, estado..."
        ),
        "es": (
            "<b>Remote Claude Pocket</b>\n\n"
            "abre miapp\n"
            "abre  (sin nombre, muestra los proyectos)\n"
            "cierra miapp\n"
            "cierra todas\n"
            "sesiones\n"
            "muestra miapp\n"
            "alias app = mi-app-de-nombre-largo\n"
            "aliases\n"
            "borra alias app\n"
            "estado\n"
            "login\n"
            "{power}"
            "\nLos nombres pueden ir incompletos: app encuentra mi-app-de-nombre-largo.\n"
            "También entiende inglés: open, close, show, status..."
        ),
    },
    "help_power": {"en": "reboot server\nshutdown server\n",
                   "es": "reinicia servidor\napaga servidor\n"},
    "menu": {"en": ["Open", "Sessions", "Status"],
             "es": ["Abrir", "Sesiones", "Estado"]},
    "btn_show": {"en": "Show", "es": "Mostrar"},
    "btn_close": {"en": "Close", "es": "Cerrar"},
    "btn_show_p": {"en": "Show {p}", "es": "Mostrar {p}"},
    "btn_close_p": {"en": "Close {p}", "es": "Cerrar {p}"},
    "btn_close_all": {"en": "Close all", "es": "Cerrar todas"},
    "btn_yes_close_all": {"en": "Yes, close all", "es": "Sí, cerrar todas"},
    "btn_yes_reboot": {"en": "Yes, reboot", "es": "Sí, reiniciar"},
    "btn_yes_shutdown": {"en": "Yes, shut down", "es": "Sí, apagar"},
    "btn_no": {"en": "No", "es": "No"},
    "btn_keep": {"en": "Keep", "es": "Mantener"},
    "btn_login": {"en": "Log in", "es": "Hacer login"},
    "btn_login_link": {"en": "Open login link", "es": "Abrir link de login"},

    "empty_screen": {"en": "(empty screen)", "es": "(pantalla vacía)"},
    "already_open": {"en": "There is already a session open in {b}.",
                     "es": "Ya hay una sesión abierta en {b}."},
    "opening": {"en": "Opening Claude in {b}...", "es": "Abriendo Claude en {b}..."},
    "opening_short": {"en": "Opening...", "es": "Abriendo..."},
    "open_failed": {"en": "Could not open {b}:\n{err}",
                    "es": "No se pudo abrir {b}:\n{err}"},
    "enabling_rc": {"en": "Enabling remote control in {b}...",
                    "es": "Activando control remoto en {b}..."},
    "died_on_start": {"en": "Claude exited on start in {b}. Last screen:\n{p}",
                      "es": "Claude se cerró al arrancar en {b}. Última pantalla:\n{p}"},
    "ready_rc": {"en": "Ready: {b} is in the Claude app.",
                 "es": "Listo: {b} está en la app de Claude."},
    "ready_plain": {"en": "Ready: Claude is running in {b}.",
                    "es": "Listo: Claude está corriendo en {b}."},
    "trusting": {"en": "Trusting the folder {b}...",
                 "es": "Aceptando confianza de carpeta en {b}..."},
    "no_rc": {"en": "Remote control did not show up in {b} after {s} s. Screen:\n{p}",
              "es": "No vi el control remoto activo en {b} tras {s} s. Pantalla:\n{p}"},
    "already_closed": {"en": "was already closed", "es": "ya estaba cerrada"},
    "closed": {"en": "closed", "es": "cerrada"},
    "force_closed": {"en": "force closed (did not answer /exit)",
                     "es": "cerrada a la fuerza (no respondió a /exit)"},
    "closing": {"en": "Closing {b}...", "es": "Cerrando {b}..."},
    "closing_short": {"en": "Closing...", "es": "Cerrando..."},
    "closing_n": {"en": "Closing {n} sessions...", "es": "Cerrando {n} sesiones..."},
    "no_sessions": {"en": "No open sessions.", "es": "No hay sesiones abiertas."},
    "no_sessions_match": {"en": "No open sessions matching «{p}».",
                          "es": "No hay sesiones abiertas que coincidan con «{p}»."},
    "preparing": {"en": "Preparing...", "es": "Preparando..."},
    "hc_paused": {"en": "Healthchecks.io paused; it resumes with the first ping.",
                  "es": "Healthchecks.io en pausa; se reactiva con el primer ping."},
    "hc_not_paused": {"en": "Could not pause Healthchecks.io: expect an alert.",
                      "es": "No pude pausar Healthchecks.io: llegará una alerta."},
    "shutting_down": {"en": "Shutting down. Use the power button to turn it on.",
                      "es": "Apagando. Para prenderlo, usa el botón de encendido."},
    "rebooting": {"en": "Rebooting. I'll tell you when it's back.",
                  "es": "Reiniciando. Te aviso cuando vuelva."},
    "power_failed": {"en": "systemctl {cmd} failed:", "es": "Falló systemctl {cmd}:"},
    "power_disabled": {"en": "Power commands are disabled (power_commands = false).",
                       "es": "Los comandos de encendido están apagados (power_commands = false)."},
    "session_gone": {"en": "That session no longer exists.",
                     "es": "Esa sesión ya no existe."},
    "open_since": {"en": "{p} · open for {t}", "es": "{p} · abierta hace {t}"},
    "not_found": {"en": "Could not find «{p}» in {dir}.",
                  "es": "No encontré «{p}» en {dir}."},
    "which_project": {"en": "Which project?", "es": "¿En qué proyecto?"},
    "which_session": {"en": "Which session?", "es": "¿Cuál sesión?"},
    "confirm_close_all": {"en": "Close all Claude sessions?",
                          "es": "¿Cierro todas las sesiones de Claude?"},
    "alias_invalid": {"en": "Aliases can only have letters, numbers, - and _, no spaces.",
                      "es": "El alias solo puede tener letras, números, - y _, sin espacios."},
    "alias_ambiguous": {"en": "«{d}» must match exactly one project. Matches: {l}.",
                        "es": "«{d}» debe coincidir con un solo proyecto. Coinciden: {l}."},
    "none": {"en": "none", "es": "ninguno"},
    "alias_set": {"en": "Alias {a} points to {p}.", "es": "Alias {a} apunta a {p}."},
    "no_aliases": {"en": "No aliases. Example: alias app = my-long-app-name",
                   "es": "No hay aliases. Ejemplo: alias app = mi-app-de-nombre-largo"},
    "alias_removed": {"en": "Alias {a} removed.", "es": "Alias {a} borrado."},
    "alias_missing": {"en": "Alias {a} does not exist.", "es": "No existe el alias {a}."},
    "confirm_reboot": {"en": "Reboot the server? All Claude sessions will be closed.",
                       "es": "¿Reinicio el servidor? Se cierran todas las sesiones de Claude."},
    "confirm_shutdown": {"en": "Shut down the server? All sessions will be closed and "
                               "you'll need the power button to turn it back on.",
                         "es": "¿Apago el servidor? Se cierran todas las sesiones y para "
                               "prenderlo hay que usar el botón de encendido."},
    "login_starting": {"en": "Starting login...", "es": "Iniciando login..."},
    "login_cancelled": {"en": "Login cancelled.", "es": "Login cancelado."},
    "not_understood": {"en": "I didn't get that. Type help for examples.",
                       "es": "No entendí. Escribe ayuda para ver ejemplos."},
    "kept": {"en": "{b}: kept open.", "es": "{b}: se mantiene abierta."},
    "cancelled": {"en": "Cancelled.", "es": "Cancelado."},
    "confirm_expired": {"en": "Confirmation expired. Ask again.",
                        "es": "Confirmación vencida. Vuelve a pedirlo."},
    "login_instructions": {
        "en": "Open the link, sign in with your Claude account and paste the code "
              "it shows you here. It expires in 10 minutes; type «cancel login» to abort.",
        "es": "Abre el link, inicia sesión con tu cuenta de Claude y pega aquí "
              "el código que te muestre. Vence en 10 minutos; "
              "escribe «cancela login» para abortar."},
    "code_received": {"en": "Code received. Verifying...",
                      "es": "Código recibido. Verificando..."},
    "login_done": {"en": "Login complete: {i}.\nIf a session still asks for login, "
                         "close it and open it again.",
                   "es": "Login completo: {i}.\nSi una sesión sigue pidiendo login, "
                         "ciérrala y ábrela de nuevo."},
    "login_failed": {"en": "Login did not complete.\n{i}",
                     "es": "El login no se completó.\n{i}"},
    "login_open_failed": {"en": "Could not open the login session: {e}",
                          "es": "No pude abrir la sesión de login: {e}"},
    "login_no_link": {"en": "Claude did not show the login link:\n{t}",
                      "es": "Claude no mostró el link de login:\n{t}"},
    "login_status_failed": {"en": "could not read claude auth status",
                            "es": "no pude leer claude auth status"},
    "login_info": {"en": "{email}, {plan} plan", "es": "{email}, plan {plan}"},
    "login_expired": {"en": "Login expired without a code. Type login to start again.",
                      "es": "El login venció sin código. Escribe login para empezar de nuevo."},
    "why_login": {"en": "Claude asks you to log in.", "es": "Claude pide iniciar sesión."},
    "why_limit": {"en": "hit the plan's usage limit.",
                  "es": "alcanzó el límite de uso del plan."},
    "why_error": {"en": "Claude shows an error.", "es": "Claude muestra un error."},
    "why_dialog": {"en": "Claude is waiting for you to pick an option.",
                   "es": "Claude espera que elijas una opción."},
    "idle": {"en": "{b}: no activity for {h} hours. Close it?",
             "es": "{b}: sin actividad hace {h} horas. ¿La cierro?"},
    "check_down": {"en": "Alert: <b>{n}</b> is having problems{d}.",
                   "es": "Alerta: <b>{n}</b> con problemas{d}."},
    "check_up": {"en": "<b>{n}</b> recovered{d}.", "es": "<b>{n}</b> recuperado{d}."},
    "session_cleaned": {"en": "Session <b>{p}</b> no longer had Claude running; cleaned up.",
                        "es": "La sesión <b>{p}</b> ya no tenía Claude corriendo; registro limpio."},
    "conflict": {"en": "Another instance is using this bot token (4 conflicts in "
                       "10 minutes). If it isn't yours, revoke the token in BotFather.",
                 "es": "Otra instancia está usando el token del bot (4 conflictos "
                       "en 10 minutos). Si no es tuya, rota el token en BotFather."},
    "bot_error": {"en": "Bot error: {e}", "es": "Error en el bot: {e}"},
    "server_online": {"en": "{host} is online ({t}).", "es": "{host} en línea ({t})."},
    "bot_restarted": {"en": "Remote Claude Pocket restarted ({t}).",
                      "es": "Remote Claude Pocket reiniciado ({t})."},
    "open_count": {"en": "Open sessions: {n}.", "es": "Sesiones abiertas: {n}."},
    "cmd_open": {"en": "Open Claude in a project", "es": "Abrir Claude en un proyecto"},
    "cmd_sessions": {"en": "List open sessions", "es": "Ver las sesiones abiertas"},
    "cmd_status": {"en": "Server status", "es": "Estado del servidor"},
    "cmd_closeall": {"en": "Close all sessions", "es": "Cerrar todas las sesiones"},
    "cmd_help": {"en": "Usage examples", "es": "Ejemplos de uso"},

    "st_uptime": {"en": "Uptime: {v}", "es": "Encendido: {v}"},
    "st_cpu": {"en": "CPU: load {l:.2f} on {n} cores", "es": "CPU: carga {l:.2f} en {n} núcleos"},
    "st_ram": {"en": "RAM: {u:.1f} of {t:.1f} GB", "es": "RAM: {u:.1f} de {t:.1f} GB"},
    "st_swap": {"en": "Swap: {u:.1f} of {t:.1f} GB", "es": "Swap: {u:.1f} de {t:.1f} GB"},
    "st_disk": {"en": "Disk: {u:.0f} of {t:.0f} GB ({p} %)",
                "es": "Disco: {u:.0f} de {t:.0f} GB ({p} %)"},
    "st_temp": {"en": "Temperature: {v:.0f} °C", "es": "Temperatura: {v:.0f} °C"},
    "st_temp_none": {"en": "Temperature: n/a", "es": "Temperatura: sin dato"},
    "st_sessions": {"en": "Claude sessions: {n}", "es": "Sesiones de Claude: {n}"},
    "st_up": {"en": "online", "es": "en línea"},
    "st_down": {"en": "DOWN", "es": "CAÍDO"},
    "st_backup": {"en": "Last backup: {v}", "es": "Último backup: {v}"},
    "st_backup_none": {"en": "no record", "es": "sin registro"},
    "st_backup_age": {"en": "{h:.0f} h ago", "es": "hace {h:.0f} h"},
    "st_alert": {"en": " (ALERT)", "es": " (ALERTA)"},
    "st_reboot": {"en": "Reboot required: {v}", "es": "Reinicio pendiente: {v}"},
    "yes": {"en": "yes", "es": "sí"},
    "no": {"en": "no", "es": "no"},
}


def t(key, **kw):
    entry = TEXTS[key]
    value = entry.get(LANG, entry["en"])
    return value.format(**kw) if kw and isinstance(value, str) else value
