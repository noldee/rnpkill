"""Banner ASCII — solo define el arte y la paleta.

El render se delega completamente al menú (`prompt_toolkit`), que lo
dibuja como primera línea del layout. Así evitamos el flash causado por
imprimir con rich y luego limpiar la pantalla.
"""
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
    """Solo guarda la paleta activa; ya no imprime nada."""

    def __init__(self, console: Console | None = None, theme: str = "default") -> None:
        self._palette: ColorPalette = get_theme(theme)
        self._console = console or Console(theme=to_rich_theme(self._palette))

    @property
    def palette(self) -> ColorPalette:
        return self._palette

    @property
    def console(self) -> Console:
        return self._console