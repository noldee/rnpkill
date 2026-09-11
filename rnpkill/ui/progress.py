"""Barra de progreso para el borrado."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from rnpkill.utils.themes import get_theme


@contextmanager
def deletion_progress(
    total: int, console: Console, theme: str = "default"
) -> Iterator[Progress]:
    """Context manager que provee una barra de progreso para el borrado.

    Args:
        total: Número total de carpetas a borrar.
        console: Console de rich.
        theme: Nombre del tema (para el color de la barra).

    Yields:
        Instancia de ``Progress`` lista para ``add_task``.
    """
    palette = get_theme(theme)
    with Progress(
        SpinnerColumn(style=palette.primary),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style=palette.success, finished_style=palette.success),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        yield progress