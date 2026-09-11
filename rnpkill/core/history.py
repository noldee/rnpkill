"""Historial de limpiezas y estadísticas agregadas.

Se guarda en ``~/.local/share/rnpkill/history.jsonl`` (una línea JSON
por evento). El formato JSONL permite añadir sin reescribir el archivo
completo, y sobrevive a corrupciones parciales.
"""
from __future__ import annotations

import csv
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from rnpkill.utils.paths import history_file


@dataclass(slots=True)
class HistoryEntry:
    """Registro de una limpieza individual."""

    timestamp: float
    freed_bytes: int
    count: int
    errors: int
    paths: list[str]

    @property
    def iso_date(self) -> str:
        """Fecha legible para mostrar."""
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(self.timestamp))


class HistoryStore:
    """Persistencia y consulta del historial."""

    def __init__(self, path: Path | None = None) -> None:
        """Inicializa el store.

        Args:
            path: Ruta al archivo JSONL. Por defecto ``history_file()``.
        """
        self._path = path or history_file()

    # ------------------------------------------------------------------ #
    # Escritura
    # ------------------------------------------------------------------ #
    def append(self, entry: HistoryEntry) -> None:
        """Añade una entrada al final del historial."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------ #
    # Lectura
    # ------------------------------------------------------------------ #
    def load_all(self) -> list[HistoryEntry]:
        """Carga todas las entradas válidas (ignora líneas corruptas)."""
        if not self._path.exists():
            return []
        entries: list[HistoryEntry] = []
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    entries.append(HistoryEntry(**data))
                except (json.JSONDecodeError, TypeError):
                    continue
        return entries

    def last(self, n: int = 10) -> list[HistoryEntry]:
        """Últimas ``n`` entradas, ordenadas de más reciente a más antigua."""
        return sorted(self.load_all(), key=lambda e: e.timestamp, reverse=True)[:n]

    def stats(self) -> dict[str, int | float]:
        """Estadísticas agregadas: total liberado, sesiones, promedio."""
        entries = self.load_all()
        if not entries:
            return {
                "sessions": 0,
                "total_freed": 0,
                "total_deleted": 0,
                "avg_per_session": 0.0,
                "first": 0.0,
                "last": 0.0,
            }
        total_freed = sum(e.freed_bytes for e in entries)
        total_deleted = sum(e.count for e in entries)
        timestamps = [e.timestamp for e in entries]
        return {
            "sessions": len(entries),
            "total_freed": total_freed,
            "total_deleted": total_deleted,
            "avg_per_session": total_freed / len(entries),
            "first": min(timestamps),
            "last": max(timestamps),
        }

    # ------------------------------------------------------------------ #
    # Exportación
    # ------------------------------------------------------------------ #
    def export_csv(self, dest: Path) -> None:
        """Exporta el historial completo a CSV."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        entries = self.load_all()
        with dest.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                ["timestamp", "iso_date", "freed_bytes", "count", "errors", "paths"]
            )
            for e in entries:
                writer.writerow(
                    [
                        e.timestamp,
                        e.iso_date,
                        e.freed_bytes,
                        e.count,
                        e.errors,
                        "|".join(e.paths),
                    ]
                )