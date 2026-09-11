"""Orquestador del flujo principal de rnpkill.

Coordina scanner, sizer, filtros, reportes, menú y deleter. Toda la
lógica de decisión vive aquí; los módulos de `core/` y `ui/` hacen el
trabajo pesado.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import questionary
from rich.console import Console
from rich.table import Table

from rnpkill.core.age_filter import AgeFilter
from rnpkill.core.deleter import DirectoryDeleter
from rnpkill.core.history import HistoryEntry, HistoryStore
from rnpkill.core.models import TargetFolder
from rnpkill.core.reporter import SessionReporter
from rnpkill.core.scanner import ProjectScanner
from rnpkill.core.size_calculator import SizeCalculator
from rnpkill.ui.banner import BANNER_ASCII
from rnpkill.ui.menu import TargetMenu
from rnpkill.ui.progress import deletion_progress
from rnpkill.utils.formatters import format_bytes
from rnpkill.utils.themes import get_theme, to_rich_theme


class RnpkillApp:
    """Orquesta el flujo completo de la aplicación."""

    def __init__(
        self,
        max_depth: int | None = None,
        skip_sizes: bool = False,
        older_than: str | None = None,
        dry_run: bool = False,
        report: str | None = None,
        theme: str = "default",
    ) -> None:
        self._theme = theme
        palette = get_theme(theme)
        self._console = Console(theme=to_rich_theme(palette))

        self._scanner = ProjectScanner(max_depth=max_depth)
        self._sizer = SizeCalculator()
        self._deleter = DirectoryDeleter()
        self._menu = TargetMenu(BANNER_ASCII, theme=theme)
        self._history = HistoryStore()
        self._age_filter = AgeFilter.from_expression(older_than)

        self._skip_sizes = skip_sizes
        self._dry_run = dry_run
        self._report = Path(report).expanduser() if report else None

    # ------------------------------------------------------------------ #
    # Flujo principal
    # ------------------------------------------------------------------ #
    def run(self, root: Path) -> int:
        """Ejecuta el flujo completo y devuelve el código de salida."""
        t0 = time.perf_counter()

        try:
            targets = self._discover_targets(root)
        except ValueError as exc:
            self._console.print(f"[red]Error:[/red] {exc}")
            return 1

        targets = self._apply_age_filter(targets)

        if not targets:
            self._console.print(
                "[yellow]No se encontraron carpetas objetivo.[/yellow]"
            )
            return 0

        scan_seconds = time.perf_counter() - t0
        total_bytes = sum(t.size_bytes for t in targets)

        if self._report:
            self._write_report(targets)

        selected = self._menu.select(
            targets,
            total_bytes=total_bytes,
            scan_seconds=scan_seconds,
        )

        if not selected:
            return 0

        if self._dry_run:
            self._print_dry_run(selected)
            return 0

        return self._confirm_and_delete(selected)

    # ------------------------------------------------------------------ #
    # Descubrimiento
    # ------------------------------------------------------------------ #
    def _discover_targets(self, root: Path) -> list[TargetFolder]:
        """Escanea y mide tamaños en paralelo."""
        projects = self._scanner.scan(root)
        targets: list[TargetFolder] = []
        for project in projects:
            targets.extend(project.targets)

        if not targets or self._skip_sizes:
            return targets

        with self._console.status(
            f"[primary]Midiendo {len(targets)} carpeta(s)...[/primary]",
            spinner="dots",
        ):
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = {
                    executor.submit(self._sizer.calculate, t.path): t
                    for t in targets
                }
                for future in as_completed(futures):
                    target = futures[future]
                    try:
                        target.size_bytes = future.result()
                    except Exception:
                        target.size_bytes = 0
        return targets

    def _apply_age_filter(
        self, targets: list[TargetFolder]
    ) -> list[TargetFolder]:
        """Aplica ``--older-than`` y avisa al usuario si filtró algo."""
        before = len(targets)
        filtered = self._age_filter.apply(targets)
        if self._age_filter._threshold is not None:
            self._console.print(
                f"[dim]Filtrado por antigüedad: {len(filtered)}/{before} "
                f"carpetas coinciden.[/dim]"
            )
        return filtered

    # ------------------------------------------------------------------ #
    # Reportes
    # ------------------------------------------------------------------ #
    def _write_report(self, targets: list[TargetFolder]) -> None:
        assert self._report is not None
        reporter = SessionReporter(targets)
        suffix = self._report.suffix.lower()
        try:
            if suffix == ".csv":
                reporter.to_csv(self._report)
            else:
                reporter.to_json(self._report)
            self._console.print(
                f"[success]Reporte guardado:[/success] {self._report}"
            )
        except OSError as exc:
            self._console.print(
                f"[danger]No se pudo guardar reporte:[/danger] {exc}"
            )

    def _print_dry_run(self, selected: list[TargetFolder]) -> None:
        table = Table(title="[bold]DRY RUN — no se borrará nada[/bold]")
        table.add_column("Tamaño", justify="right", style="primary")
        table.add_column("Ruta")
        for t in sorted(selected, key=lambda x: -x.size_bytes):
            table.add_row(format_bytes(t.size_bytes), str(t.path))
        self._console.print(table)

    # ------------------------------------------------------------------ #
    # Confirmación y borrado
    # ------------------------------------------------------------------ #
    def _confirm_and_delete(self, selected: list[TargetFolder]) -> int:
        total = sum(t.size_bytes for t in selected)
        self._console.print(
            f"\n[bold]Se eliminarán [danger]{len(selected)}[/danger] carpetas "
            f"([primary]{format_bytes(total)}[/primary]).[/bold]"
        )

        if not questionary.confirm("¿Continuar?", default=False).ask():
            self._console.print("[yellow]Cancelado.[/yellow]")
            return 0

        freed, errors, deleted_paths = self._delete_all(selected)
        self._record_history(freed, errors, deleted_paths)
        self._print_summary(freed, errors)

        return 2 if errors else 0

    def _delete_all(
        self, selected: list[TargetFolder]
    ) -> tuple[int, int, list[str]]:
        """Borra todas las carpetas y devuelve (liberado, errores, rutas)."""
        freed = 0
        errors = 0
        deleted_paths: list[str] = []

        with deletion_progress(
            len(selected), self._console, self._theme
        ) as progress:
            task = progress.add_task("Eliminando…", total=len(selected))
            for target in selected:
                progress.update(task, description=f"→ {target.display_name}")
                result = self._deleter.delete(target.path, target.size_bytes)
                if result.success:
                    freed += result.freed_bytes
                    deleted_paths.append(str(target.path))
                else:
                    errors += 1
                    progress.console.print(
                        f"[danger]✗[/danger] {target.display_name} — "
                        f"{result.error}"
                    )
                progress.advance(task)
        return freed, errors, deleted_paths

    def _record_history(
        self, freed: int, errors: int, paths: list[str]
    ) -> None:
        """Persiste la sesión en el historial (best-effort)."""
        if not paths:
            return
        try:
            self._history.append(
                HistoryEntry(
                    timestamp=time.time(),
                    freed_bytes=freed,
                    count=len(paths),
                    errors=errors,
                    paths=paths,
                )
            )
        except OSError:
            pass  # historial es opcional

    def _print_summary(self, freed: int, errors: int) -> None:
        line = f"\n[bold success]Liberado: {format_bytes(freed)}[/bold success]"
        if errors:
            line += f"   [danger]Errores: {errors}[/danger]"
        self._console.print(line)