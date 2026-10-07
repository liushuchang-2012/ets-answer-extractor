import json
import os
import sys
from pathlib import Path

CONFIG_NAME = "ets-config.json"


def project_dir():
    return os.path.dirname(os.path.abspath(__file__))


def config_path():
    return os.path.join(project_dir(), CONFIG_NAME)


def default_root():
    home = Path.home()
    if sys.platform.startswith("win"):
        return str(home / "AppData" / "Roaming" / "ETS")
    return str(home / "ETS")


def load_root():
    cp = config_path()
    if os.path.isfile(cp):
        try:
            with open(cp, encoding="utf-8") as f:
                data = json.load(f)
            d = data.get("root", "")
            if d and os.path.isdir(d):
                return d
        except Exception:
            pass
    return default_root()


def save_root(d):
    d = os.path.abspath(os.path.expandvars(os.path.expanduser(d)))
    if not os.path.isdir(d):
        raise ValueError("目录不存在: " + d)
    with open(config_path(), "w", encoding="utf-8") as f:
        json.dump({"root": d}, f, ensure_ascii=False, indent=2)
    return d


def reset_root():
    cp = config_path()
    if os.path.isfile(cp):
        try:
            os.remove(cp)
        except OSError:
            pass
    return default_root()
