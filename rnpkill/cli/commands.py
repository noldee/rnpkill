"""Comandos auxiliares que no ejecutan el flujo principal.

- ``--history``      → últimas limpiezas
- ``--stats``        → estadísticas agregadas
- ``--export-history`` → exportar el historial completo a CSV
"""
from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table

from rnpkill.core.history import HistoryStore
from rnpkill.utils.formatters import format_bytes


def show_history(console: Console) -> int:
    """Muestra las últimas 10 limpiezas."""
    entries = HistoryStore().last(10)
    if not entries:
        console.print("[dim]Sin historial todavía.[/dim]")
        return 0

    table = Table(title="Últimas 10 limpiezas")
    table.add_column("Fecha", style="primary")
    table.add_column("Carpetas", justify="right")
    table.add_column("Liberado", justify="right", style="success")
    table.add_column("Errores", justify="right", style="danger")

    for e in entries:
        table.add_row(
            e.iso_date,
            str(e.count),
            format_bytes(e.freed_bytes),
            str(e.errors),
        )
    console.print(table)
    return 0


def show_stats(console: Console) -> int:
    """Muestra estadísticas históricas agregadas."""
    s = HistoryStore().stats()
    if s["sessions"] == 0:
        console.print("[dim]Sin estadísticas todavía.[/dim]")
        return 0

    table = Table(title="Estadísticas históricas")
    table.add_column("Métrica", style="primary")
    table.add_column("Valor", justify="right", style="success")
    table.add_row("Sesiones", str(s["sessions"]))
    table.add_row("Total carpetas borradas", str(s["total_deleted"]))
    table.add_row("Total liberado", format_bytes(int(s["total_freed"])))
    table.add_row("Promedio por sesión", format_bytes(int(s["avg_per_session"])))
    console.print(table)
    return 0


def export_history(console: Console, dest: str) -> int:
    """Exporta el historial completo a un archivo CSV."""
    path = Path(dest).expanduser()
    try:
        HistoryStore().export_csv(path)
        console.print(f"[success]Historial exportado:[/success] {path}")
        return 0
    except OSError as exc:
        console.print(f"[danger]Error al exportar:[/danger] {exc}")
        return 1