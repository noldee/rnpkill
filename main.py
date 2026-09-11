"""Punto de entrada de rnpkill — composition root."""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from rnpkill.core.age_filter import AgeFilter, AgeFilterError
from rnpkill.core.deleter import DirectoryDeleter
from rnpkill.core.history import HistoryEntry, HistoryStore
from rnpkill.core.models import TargetFolder
from rnpkill.core.reporter import SessionReporter
from rnpkill.core.scanner import ProjectScanner
from rnpkill.core.size_calculator import SizeCalculator
from rnpkill.ui.banner import BANNER_ASCII, Banner
from rnpkill.ui.menu import TargetMenu
from rnpkill.ui.progress import deletion_progress
from rnpkill.utils.formatters import format_bytes
from rnpkill.utils.paths import clear_terminal, resolve_user_path
from rnpkill.utils.themes import list_theme_names, to_rich_theme, get_theme


# ---------------------------------------------------------------------- #
# Argumentos
# ---------------------------------------------------------------------- #
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="rnpkill",
        description="Busca y elimina carpetas pesadas de desarrollo.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Raíz a escanear.")
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument("--no-size", action="store_true",
                        help="No calcular tamaños (listado instantáneo).")
    parser.add_argument("--older-than", default=None,
                        help="Solo carpetas sin tocar en X (ej: 90d, 6m, 1y).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostrar qué se borraría sin tocar nada.")
    parser.add_argument("--report", default=None,
                        help="Ruta de salida para reporte (.json o .csv).")
    parser.add_argument("--theme", default="default",
                        choices=list_theme_names(),
                        help="Tema de color de la UI.")
    parser.add_argument("--history", action="store_true",
                        help="Mostrar las últimas 10 limpiezas y salir.")
    parser.add_argument("--stats", action="store_true",
                        help="Mostrar estadísticas agregadas y salir.")
    parser.add_argument("--export-history", default=None,
                        help="Exportar historial completo a CSV y salir.")
    return parser.parse_args()


# ---------------------------------------------------------------------- #
# App
# ---------------------------------------------------------------------- #
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
        self._banner = Banner(self._console, theme=theme)
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
    def run(self, root: Path) -> int:
        self._banner.render()

        try:
            targets = self._discover_targets(root)
        except ValueError as exc:
            self._console.print(f"[danger]Error:[/danger] {exc}")
            return 1

        # Filtro por antigüedad
        before = len(targets)
        targets = self._age_filter.apply(targets)
        if self._age_filter._threshold is not None:
            self._console.print(
                f"[dim]Filtrado por antigüedad: {len(targets)}/{before} "
                f"carpetas coinciden.[/dim]"
            )

        if not targets:
            self._console.print("[yellow]No se encontraron carpetas.[/yellow]")
            return 0

        # Reporte opcional
        if self._report:
            self._write_report(targets)

        total = sum(t.size_bytes for t in targets)
        summary = (
            f"Espacio total: {format_bytes(total)} · "
            f"{len(targets)} carpeta(s)"
            + (" · DRY RUN" if self._dry_run else "")
        )

        clear_terminal()
        selected = self._menu.select(targets, summary=summary)

        if not selected:
            self._console.print("[yellow]Nada seleccionado.[/yellow]")
            return 0

        if self._dry_run:
            self._print_dry_run(selected)
            return 0

        return self._confirm_and_delete(selected)

    # ------------------------------------------------------------------ #
    def _discover_targets(self, root: Path) -> list[TargetFolder]:
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
            self._console.print(f"[success]Reporte guardado:[/success] {self._report}")
        except OSError as exc:
            self._console.print(f"[danger]No se pudo guardar reporte:[/danger] {exc}")

    def _print_dry_run(self, selected: list[TargetFolder]) -> None:
        table = Table(title="[bold]DRY RUN — no se borrará nada[/bold]")
        table.add_column("Tamaño", justify="right", style="primary")
        table.add_column("Ruta")
        for t in sorted(selected, key=lambda x: -x.size_bytes):
            table.add_row(format_bytes(t.size_bytes), str(t.path))
        self._console.print(table)

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

        freed = 0
        errors = 0
        deleted_paths: list[str] = []

        with deletion_progress(len(selected), self._console, self._theme) as progress:
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
                        f"[danger]✗[/danger] {target.display_name} — {result.error}"
                    )
                progress.advance(task)

        # Persistir en historial
        if deleted_paths:
            try:
                self._history.append(
                    HistoryEntry(
                        timestamp=__import__("time").time(),
                        freed_bytes=freed,
                        count=len(deleted_paths),
                        errors=errors,
                        paths=deleted_paths,
                    )
                )
            except OSError:
                pass  # el historial es best-effort

        self._console.print(
            f"\n[bold success]Liberado: {format_bytes(freed)}[/bold success]"
            + (f"   [danger]Errores: {errors}[/danger]" if errors else "")
        )
        return 2 if errors else 0


# ---------------------------------------------------------------------- #
# Comandos auxiliares: --history / --stats / --export-history
# ---------------------------------------------------------------------- #
def _cmd_history(console: Console) -> int:
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
        table.add_row(e.iso_date, str(e.count), format_bytes(e.freed_bytes), str(e.errors))
    console.print(table)
    return 0


def _cmd_stats(console: Console) -> int:
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


def _cmd_export_history(console: Console, dest: str) -> int:
    path = Path(dest).expanduser()
    try:
        HistoryStore().export_csv(path)
        console.print(f"[success]Historial exportado:[/success] {path}")
        return 0
    except OSError as exc:
        console.print(f"[danger]Error al exportar:[/danger] {exc}")
        return 1


# ---------------------------------------------------------------------- #
# Entry point
# ---------------------------------------------------------------------- #
def main() -> int:
    args = _parse_args()
    console = Console(theme=to_rich_theme(get_theme(args.theme)))

    if args.history:
        return _cmd_history(console)
    if args.stats:
        return _cmd_stats(console)
    if args.export_history:
        return _cmd_export_history(console, args.export_history)

    root = resolve_user_path(args.path)
    try:
        app = RnpkillApp(
            max_depth=args.max_depth,
            skip_sizes=args.no_size,
            older_than=args.older_than,
            dry_run=args.dry_run,
            report=args.report,
            theme=args.theme,
        )
        return app.run(root)
    except AgeFilterError as exc:
        console.print(f"[danger]Error en --older-than:[/danger] {exc}")
        return 1
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrumpido.[/yellow]")
        return 130


if __name__ == "__main__":
    sys.exit(main())