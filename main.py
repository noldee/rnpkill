"""Punto de entrada de rnpkill.

Actúa como *composition root*: instancia los colaboradores y orquesta
el flujo, delegando toda la lógica a las capas `core` y `ui`.
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import questionary
from rich.console import Console

from rnpkill.core.deleter import DirectoryDeleter
from rnpkill.core.models import TargetFolder
from rnpkill.core.scanner import ProjectScanner
from rnpkill.core.size_calculator import SizeCalculator
from rnpkill.ui.banner import BANNER_ASCII, Banner
from rnpkill.ui.menu import TargetMenu
from rnpkill.utils.formatters import format_bytes
from rnpkill.utils.paths import clear_terminal, resolve_user_path


def _parse_args() -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        prog="rnpkill",
        description="Busca y elimina carpetas pesadas de desarrollo "
        "(node_modules, venv, .venv, env).",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directorio raíz donde escanear (default: cwd).",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Profundidad máxima de recursión.",
    )
    parser.add_argument(
        "--no-size",
        action="store_true",
        help="No calcular tamaños (listado instantáneo).",
    )
    return parser.parse_args()


class RnpkillApp:
    """Orquesta el flujo completo de la aplicación."""

    def __init__(
        self,
        max_depth: int | None = None,
        skip_sizes: bool = False,
    ) -> None:
        self._console = Console()
        self._banner = Banner(self._console)
        self._scanner = ProjectScanner(max_depth=max_depth)
        self._sizer = SizeCalculator()
        self._deleter = DirectoryDeleter()
        self._menu = TargetMenu(BANNER_ASCII)
        self._skip_sizes = skip_sizes

    # ------------------------------------------------------------------ #
    # Flujo principal
    # ------------------------------------------------------------------ #
    def run(self, root: Path) -> int:
        """Ejecuta el flujo completo y devuelve el código de salida."""
        self._banner.render()

        try:
            targets = self._discover_targets(root)
        except ValueError as exc:
            self._console.print(f"[red]Error:[/red] {exc}")
            return 1

        if not targets:
            self._console.print(
                "[yellow]No se encontraron carpetas objetivo.[/yellow]"
            )
            return 0

        # Construir el resumen que se mostrará fijo bajo el banner del menú.
        total = sum(t.size_bytes for t in targets)
        summary = (
            f"Espacio total encontrado: {format_bytes(total)} "
            f"en {len(targets)} carpeta(s)."
        )

        # Limpiar pantalla antes de lanzar el menú interactivo.
        # El menú (prompt_toolkit) dibuja su propio banner fijo arriba.
        clear_terminal()
        selected = self._menu.select(targets, summary=summary)

        if not selected:
            self._console.print("[yellow]Nada seleccionado. Saliendo.[/yellow]")
            return 0

        return self._confirm_and_delete(selected)

    # ------------------------------------------------------------------ #
    # Pasos internos
    # ------------------------------------------------------------------ #
    def _discover_targets(self, root: Path) -> list[TargetFolder]:
        """Escanea, mide tamaños y devuelve la lista ordenada por tamaño."""
        projects = self._scanner.scan(root)
        targets: list[TargetFolder] = []

        for project in projects:
            targets.extend(project.targets)

        if not targets:
            return []

        if self._skip_sizes:
            return targets  # listado instantáneo, sin medir

        with self._console.status(
            f"[cyan]Midiendo {len(targets)} carpeta(s)...[/cyan]",
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

        return sorted(targets, key=lambda t: t.size_bytes, reverse=True)

    def _confirm_and_delete(self, selected: list[TargetFolder]) -> int:
        """Confirma y elimina. Devuelve 0 si todo OK, 2 si hubo errores."""
        total = sum(t.size_bytes for t in selected)
        self._console.print(
            f"\n[bold]Se eliminarán [red]{len(selected)}[/red] carpetas "
            f"([magenta]{format_bytes(total)}[/magenta]).[/bold]"
        )

        if not questionary.confirm("¿Continuar?", default=False).ask():
            self._console.print("[yellow]Operación cancelada.[/yellow]")
            return 0

        freed = 0
        errors = 0
        for target in selected:
            result = self._deleter.delete(target.path, target.size_bytes)
            if result.success:
                freed += result.freed_bytes
                self._console.print(f"[green]✓[/green] {target.display_name}")
            else:
                errors += 1
                self._console.print(
                    f"[red]✗[/red] {target.display_name} — {result.error}"
                )

        self._console.print(
            f"\n[bold green]Liberado: {format_bytes(freed)}[/bold green]"
            + (f"   [red]Errores: {errors}[/red]" if errors else "")
        )
        return 2 if errors else 0


# ---------------------------------------------------------------------- #
# Entry point
# ---------------------------------------------------------------------- #
def main() -> int:
    args = _parse_args()
    root = resolve_user_path(args.path)
    try:
        app = RnpkillApp(max_depth=args.max_depth, skip_sizes=args.no_size)
        return app.run(root)
    except KeyboardInterrupt:
        print("\n[Interrumpido por el usuario]")
        return 130


if __name__ == "__main__":
    sys.exit(main())