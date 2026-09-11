"""Modelos de dominio de rnpkill."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class TargetFolder:
    """Representa una carpeta pesada de desarrollo detectada.

    Attributes:
        name: Nombre del directorio (``node_modules``, ``venv``, etc.).
        path: Ruta absoluta al directorio.
        size_bytes: Tamaño ocupado en bytes.
        mtime: Timestamp de modificación (segundos epoch).
    """

    name: str
    path: Path
    size_bytes: int = 0
    mtime: float = 0.0

    @property
    def display_name(self) -> str:
        """Nombre legible incluyendo el proyecto padre."""
        return f"{self.path.parent.name}/{self.name}"


@dataclass(slots=True)
class Project:
    """Proyecto detectado que contiene una o más carpetas objetivo."""

    path: Path
    targets: list[TargetFolder] = field(default_factory=list)

    @property
    def total_size(self) -> int:
        """Suma de bytes de todas las carpetas objetivo del proyecto."""
        return sum(target.size_bytes for target in self.targets)