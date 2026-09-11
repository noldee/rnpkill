"""Formateo de magnitudes."""
from __future__ import annotations

_UNITS = ("B", "KB", "MB", "GB", "TB", "PB")


def format_bytes(size_bytes: int) -> str:
    """Convierte bytes a una cadena legible (``1.24 GB``, ``512 MB``).

    Args:
        size_bytes: Tamaño en bytes. Debe ser no negativo.

    Returns:
        Cadena con 2 decimales y unidad correspondiente.
    """
    if size_bytes < 0:
        raise ValueError("El tamaño no puede ser negativo")
    if size_bytes == 0:
        return "0 B"

    size = float(size_bytes)
    index = 0
    while size >= 1024.0 and index < len(_UNITS) - 1:
        size /= 1024.0
        index += 1

    return f"{size:.2f} {_UNITS[index]}"