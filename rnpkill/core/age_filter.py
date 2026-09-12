"""Filtro por antigüedad para carpetas objetivo.

Permite al usuario filtrar por ``--older-than 90d`` para mostrar solo
lo que no se ha tocado en ese periodo. Acepta sufijos ``h``, ``d``,
``w``, ``m``, ``y``.
"""
from __future__ import annotations

import re
import time

from rnpkill.core.models import TargetFolder

_PATTERN = re.compile(r"^(\d+)\s*([hdwmy]?)$", re.IGNORECASE)

_UNIT_SECONDS = {
    "h": 3600,
    "d": 86400,
    "w": 604800,
    "m": 2592000,   # 30 días
    "y": 31536000,  # 365 días
}


class AgeFilterError(ValueError):
    """Error al parsear la expresión de antigüedad."""


def parse_age(expr: str) -> float:
    """Convierte ``90d`` → 7776000.0 segundos.

    Args:
        expr: Cadena tipo ``30``, ``90d``, ``2w``, ``6m``, ``1y``.

    Returns:
        Cantidad de segundos.

    Raises:
        AgeFilterError: Si la expresión no es válida.
    """
    match = _PATTERN.match(expr.strip())
    if not match:
        raise AgeFilterError(
            f"Formato inválido: '{expr}'. Usa ej: 30, 90d, 2w, 6m, 1y."
        )
    value = int(match.group(1))
    unit = (match.group(2) or "d").lower()
    return value * _UNIT_SECONDS[unit]


class AgeFilter:
    """Filtra carpetas por fecha de modificación."""

    def __init__(self, older_than_seconds: float | None = None) -> None:
        """Inicializa el filtro.

        Args:
            older_than_seconds: Umbral en segundos. ``None`` = sin filtro.
        """
        self._threshold = older_than_seconds

    @property
    def is_active(self) -> bool:
        """True si hay un umbral configurado (es decir, --older-than se usó)."""
        return self._threshold is not None

    @classmethod
    def from_expression(cls, expr: str | None) -> "AgeFilter":
        """Construye el filtro desde una expresión CLI."""
        if not expr:
            return cls(None)
        return cls(parse_age(expr))

    def apply(self, targets: list[TargetFolder]) -> list[TargetFolder]:
        """Devuelve solo las carpetas más antiguas que el umbral.

        Args:
            targets: Lista a filtrar.

        Returns:
            Sub-lista filtrada (o la original si no hay umbral).
        """
        if self._threshold is None:
            return targets

        cutoff = time.time() - self._threshold
        return [t for t in targets if t.mtime > 0 and t.mtime < cutoff]