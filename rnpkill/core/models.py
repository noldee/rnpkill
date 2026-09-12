"""Modelos de dominio de rnpkill."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class TargetFolder:
    """..."""
    name: str
    path: Path
    size_bytes: int = 0
    mtime: float = 0.0
    measuring: bool = False
    measure_error: str | None = None

    # ─── Estado de borrado ───────────────────────────────────────
    # None          → no está borrándose ni se ha borrado
    # "deleting"    → en proceso
    # "done"        → borrado exitoso
    # "error"       → falló (con mensaje en delete_error)
    deleting_state: str | None = None
    delete_error: str | None = None

    @property
    def display_name(self) -> str:
        return f"{self.path.parent.name}/{self.name}"

    @property
    def is_measured(self) -> bool:
        return not self.measuring and self.measure_error is None

    @property
    def is_deleting(self) -> bool:
        return self.deleting_state == "deleting"

    @property
    def is_deleted(self) -> bool:
        return self.deleting_state == "done"

    @property
    def has_delete_error(self) -> bool:
        return self.deleting_state == "error"


@dataclass(slots=True)
class Project:
    """Proyecto detectado que contiene una o más carpetas objetivo."""

    path: Path
    targets: list[TargetFolder] = field(default_factory=list)

    @property
    def total_size(self) -> int:
        """Suma de bytes de todas las carpetas objetivo del proyecto."""
        return sum(target.size_bytes for target in self.targets)