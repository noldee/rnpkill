"""Menú interactivo — orquestador delgado.

Une NavigationState + LayoutBuilder + MenuRenderer + KeyBindings.
La lógica real vive en los módulos vecinos; aquí solo se compone todo.
"""
from __future__ import annotations

from typing import Sequence

from prompt_toolkit import Application

from rnpkill.core.models import TargetFolder
from rnpkill.ui.keybindings import build_keybindings
from rnpkill.ui.layout_builder import LayoutBuilder
from rnpkill.ui.navigation import NavigationState
from rnpkill.ui.renderer import MenuRenderer
from rnpkill.utils.formatters import format_bytes
from rnpkill.utils.themes import ColorPalette, get_theme, to_prompt_style


class TargetMenu:
    """Menú interactivo: banner, árbol plegable, temas y búsqueda."""

    def __init__(self, banner_ascii: str, theme: str = "default") -> None:
        self._banner = banner_ascii.rstrip("\n")
        self._banner_lines = self._banner.count("\n") + 1
        self._palette: ColorPalette = get_theme(theme)

        self._state = NavigationState()
        self._renderer = MenuRenderer(
            banner=self._banner,
            summary_left="",
            summary_right="",
            compact_mode=False,
        )
        self._layout_builder = LayoutBuilder(self._renderer, self._banner_lines)
        self._result: list[TargetFolder] = []

    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #
    def select(
        self,
        targets: Sequence[TargetFolder],
        total_bytes: int = 0,
        scan_seconds: float = 0.0,
        order: str = "size",
    ) -> list[TargetFolder]:
        """Muestra el menú y devuelve las carpetas marcadas."""
        self._state.load(targets)
        self._state.set_order(order)

        # El renderer necesita el summary actualizado
        self._renderer = MenuRenderer(
            banner=self._banner,
            summary_left=f"{len(targets)} carpeta(s) · {format_bytes(total_bytes)}",
            summary_right=f"scan: {scan_seconds:.2f}s",
            compact_mode=False,
        )
        self._layout_builder = LayoutBuilder(self._renderer, self._banner_lines)
        self._layout_builder.recalculate()

        self._result = []

        app = Application(
            layout=self._layout_builder.build(self._state),
            key_bindings=build_keybindings(self._state, self._on_confirm),
            style=to_prompt_style(self._palette),
            full_screen=True,
            mouse_support=False,
        )
        app.run()
        return self._result

    # ------------------------------------------------------------------ #
    # Callback de confirmación
    # ------------------------------------------------------------------ #
    def _on_confirm(self, event, abort: bool = False) -> None:
        """Se dispara con ``enter``, ``q``, ``esc`` o ``Ctrl+C``."""
        self._result = [] if abort else self._state.selected_targets()
        event.app.exit()