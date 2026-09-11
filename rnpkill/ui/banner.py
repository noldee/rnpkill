"""Banner ASCII con soporte de temas."""
from __future__ import annotations

from rich.console import Console

from rnpkill.utils.themes import ColorPalette, get_theme, to_rich_theme

BANNER_ASCII = r"""
██████╗ ███╗   ██╗██████╗ ██╗  ██╗██╗██╗     ██╗
██╔══██╗████╗  ██║██╔══██╗██║ ██╔╝██║██║     ██║
██████╔╝██╔██╗ ██║██████╔╝█████╔╝ ██║██║     ██║
██╔══██╗██║╚██╗██║██╔═══╝ ██╔═██╗ ██║██║     ██║
██║  ██║██║ ╚████║██║     ██║  ██╗██║███████╗███████╗
╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝
""".strip("\n")


class Banner:
    """Renderiza el banner de bienvenida con el tema activo."""

    def __init__(self, console: Console | None = None, theme: str = "default") -> None:
        """Inicializa el banner.

        Args:
            console: Console de rich (opcional, se crea uno si falta).
            theme: Nombre del tema a usar.
        """
        self._palette: ColorPalette = get_theme(theme)
        self._console = console or Console(theme=to_rich_theme(self._palette))

    def render(self) -> None:
        """Imprime el banner con la paleta del tema."""
        self._console.print(f"[banner]{BANNER_ASCII}[/banner]")
        self._console.print(
            "[dim]  Busca y elimina carpetas pesadas de desarrollo "
            "(node_modules, venv, .venv, env)[/dim]\n"
        )

    @property
    def palette(self) -> ColorPalette:
        """Paleta activa (útil para pasarla al menú)."""
        return self._palette