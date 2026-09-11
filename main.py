"""Punto de entrada de rnpkill.

Solo enruta entre los comandos auxiliares y el flujo principal.
Toda la lógica vive en ``rnpkill.cli``.
"""
from __future__ import annotations

import sys

from rich.console import Console

from rnpkill.cli.app import RnpkillApp
from rnpkill.cli.args import parse_args
from rnpkill.cli.commands import export_history, show_history, show_stats
from rnpkill.core.age_filter import AgeFilterError
from rnpkill.utils.paths import resolve_user_path
from rnpkill.utils.themes import get_theme, to_rich_theme


def main() -> int:
    """Entry point del CLI."""
    args = parse_args()
    console = Console(theme=to_rich_theme(get_theme(args.theme)))

    # ── Comandos auxiliares (no ejecutan el flujo principal) ─────
    if args.history:
        return show_history(console)
    if args.stats:
        return show_stats(console)
    if args.export_history:
        return export_history(console, args.export_history)

    # ── Flujo principal ──────────────────────────────────────────
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