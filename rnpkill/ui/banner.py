"""Banner ASCII y encabezados de la aplicación."""
from __future__ import annotations

from rich.console import Console

BANNER_ASCII = r"""
██████╗ ███╗   ██╗██████╗ ██╗  ██╗██╗██╗     ██╗
██╔══██╗████╗  ██║██╔══██╗██║ ██╔╝██║██║     ██║
██████╔╝██╔██╗ ██║██████╔╝█████╔╝ ██║██║     ██║
██╔══██╗██║╚██╗██║██╔═══╝ ██╔═██╗ ██║██║     ██║
██║  ██║██║ ╚████║██║     ██║  ██╗██║███████╗███████╗
╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝
""".strip("\n")


class Banner:
    """Renderiza el banner de bienvenida (con rich)."""

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or Console()

    def render(self) -> None:
        """Imprime el banner decorado antes del escaneo."""
        self._console.print(f"[bold cyan]{BANNER_ASCII}[/bold cyan]")
        self._console.print(
            "[dim]  Busca y elimina carpetas pesadas de desarrollo "
            "(node_modules, venv, .venv, env)[/dim]\n"
        )