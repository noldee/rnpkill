"""Helpers de rutas multiplataforma y utilidades de terminal."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def resolve_user_path(raw: str) -> Path:
    """Expande ``~`` y variables de entorno, y resuelve a ruta absoluta."""
    expanded = os.path.expandvars(os.path.expanduser(raw))
    return Path(expanded).resolve()


def is_windows() -> bool:
    """True si se ejecuta sobre Windows."""
    return sys.platform.startswith("win")


def clear_terminal() -> None:
    """Limpia pantalla y scrollback de forma multiplataforma."""
    sys.stdout.write("\033[2J\033[3J\033[H")
    sys.stdout.flush()


def _xdg_dir(env_var: str, fallback: str) -> Path:
    """Devuelve un directorio XDG, o el fallback en macOS/Windows."""
    value = os.environ.get(env_var)
    if value:
        return Path(value).expanduser()
    return Path(fallback).expanduser()


def config_dir() -> Path:
    """Directorio de configuración de rnpkill."""
    if is_windows():
        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return Path(base) / "rnpkill"
    return _xdg_dir("XDG_CONFIG_HOME", "~/.config") / "rnpkill"


def data_dir() -> Path:
    """Directorio de datos (historial, stats)."""
    if is_windows():
        base = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        return Path(base) / "rnpkill"
    return _xdg_dir("XDG_DATA_HOME", "~/.local/share") / "rnpkill"


def cache_dir() -> Path:
    """Directorio de caché."""
    if is_windows():
        base = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        return Path(base) / "rnpkill" / "cache"
    return _xdg_dir("XDG_CACHE_HOME", "~/.cache") / "rnpkill"


def history_file() -> Path:
    """Ruta del archivo JSONL de historial."""
    return data_dir() / "history.jsonl"