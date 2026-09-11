"""Helpers de rutas multiplataforma y utilidades de terminal."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def resolve_user_path(raw: str) -> Path:
    """Expande ``~`` y variables de entorno, y resuelve a ruta absoluta.

    Args:
        raw: Ruta introducida por el usuario (puede contener ``~``).

    Returns:
        Ruta absoluta resuelta.
    """
    expanded = os.path.expandvars(os.path.expanduser(raw))
    return Path(expanded).resolve()


def is_windows() -> bool:
    """True si se ejecuta sobre Windows."""
    return sys.platform.startswith("win")


def clear_terminal() -> None:
    """Limpia pantalla y scrollback de forma multiplataforma.

    Usa códigos ANSI explícitos en lugar de ``rich.Console.clear()``
    porque este último no siempre surte efecto cuando se invoca en
    medio de la ejecución de la aplicación.

    Secuencias usadas:
        - ``\\033[2J`` → borra la pantalla visible.
        - ``\\033[3J`` → borra el scrollback (buffer de líneas previas).
        - ``\\033[H``  → mueve el cursor a home (0,0).
    """
    sys.stdout.write("\033[2J\033[3J\033[H")
    sys.stdout.flush()