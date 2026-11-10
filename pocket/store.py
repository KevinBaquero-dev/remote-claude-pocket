"""Small JSON stores in the state dir: aliases, recent projects and the
registry of open sessions."""
import json
import os
import time

from . import config
from .commands import norm


def _file(name):
    return config.state_dir() / name


def read(name):
    path = _file(name)
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        path.replace(path.with_suffix(".bad"))
        return {}


def write(name, data):
    path = _file(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    os.replace(tmp, path)


def _data():
    d = read("data.json")
    d.setdefault("aliases", {})
    d.setdefault("recent", {})
    return d


def aliases():
    return _data()["aliases"]


def set_alias(alias, project):
    d = _data()
    d["aliases"][norm(alias)] = project
    write("data.json", d)


def remove_alias(alias):
    d = _data()
    if d["aliases"].pop(norm(alias), None) is None:
        return False
    write("data.json", d)
    return True


def mark_opened(project):
    d = _data()
    d["recent"][project] = int(time.time())
    write("data.json", d)


def recent():
    return _data()["recent"]
