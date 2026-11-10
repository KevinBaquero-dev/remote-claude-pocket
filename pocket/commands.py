"""Turns free text (English or Spanish) into an action and an argument."""
import re
import unicodedata


def norm(t):
    t = unicodedata.normalize("NFD", t.lower().strip())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


PATTERNS = [
    (r"^(cancel|cancela|cancelar)\s+(the\s+|el\s+)?login$", "cancel_login"),
    (r"^(login|log in|inicia sesion|iniciar sesion)$", "login"),
    (r"^(reboot|restart|reinicia|reiniciar)(\s+the|\s+el)?\s+(server|servidor)$", "reboot"),
    (r"^(shutdown|shut down|power off|apaga|apagar)(\s+the|\s+el)?\s+(server|servidor)$",
     "shutdown"),
    (r"^(remove|delete|borra|borrar|quita|quitar)\s+alias\s+(?P<p>.+)$", "remove_alias"),
    (r"^alias(es)?$", "aliases"),
    (r"^alias\s+(?P<p>.+=.+)$", "alias"),
    (r"^(open|abre|abrir)(\s+claude)?(\s+(in|en))?(\s+(?P<p>.+))?$", "open"),
    (r"^(close|cierra|cerrar)\s+(all|todas)(\s+(sessions|las\s+sesiones))?$", "close_all"),
    (r"^(close|cierra|cerrar)(\s+claude)?(\s+(in|en))?\s+(?P<p>.+)$", "close"),
    (r"^(show|muestra|mostrar)(\s+(?P<p>.+))?$", "show"),
    (r"^(sessions|sesiones)$", "sessions"),
    (r"^(status|estado)$", "status"),
    (r"^(help|ayuda|start)$", "help"),
]
PATTERNS = [(re.compile(rx), action) for rx, action in PATTERNS]

# Slash commands (both languages) -> action.
SLASH = {"start": "help", "help": "help", "ayuda": "help",
         "open": "open", "abrir": "open",
         "sessions": "sessions", "sesiones": "sessions",
         "status": "status", "estado": "status",
         "closeall": "close_all", "cerrartodas": "close_all",
         "login": "login"}


def parse(text):
    """Returns (action, argument) or (None, "")."""
    t = norm(text)
    for rx, action in PATTERNS:
        m = rx.match(t)
        if m:
            return action, (m.groupdict().get("p") or "").strip()
    return None, ""
