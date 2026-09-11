"""Exportación de reportes de una sesión (JSON / CSV)."""
from __future__ import annotations

import csv
import json
import time
from dataclasses import asdict
from pathlib import Path

from rnpkill.core.models import TargetFolder


class SessionReporter:
    """Genera reportes de la sesión actual (lo escaneado o lo borrado)."""

    def __init__(self, targets: list[TargetFolder]) -> None:
        """Inicializa con la lista de carpetas de la sesión."""
        self._targets = targets

    def to_json(self, dest: Path) -> None:
        """Escribe un JSON con la sesión completa.

        Args:
            dest: Ruta de destino. Se crea el directorio padre si falta.
        """
        dest.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": time.time(),
            "total_count": len(self._targets),
            "total_bytes": sum(t.size_bytes for t in self._targets),
            "targets": [
                {
                    "name": t.name,
                    "path": str(t.path),
                    "parent": t.path.parent.name,
                    "size_bytes": t.size_bytes,
                    "mtime": t.mtime,
                }
                for t in self._targets
            ],
        }
        dest.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def to_csv(self, dest: Path) -> None:
        """Escribe un CSV con una fila por carpeta."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["name", "path", "parent", "size_bytes", "mtime"])
            for t in self._targets:
                writer.writerow(
                    [t.name, str(t.path), t.path.parent.name, t.size_bytes, t.mtime]
                )