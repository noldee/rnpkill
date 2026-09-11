"""Construcción del layout de prompt_toolkit.

Aquí vive el "cómo se ven los widgets" (HSplit, Window, alturas).
El cómo se pinta el texto está en renderer.py.
"""
from __future__ import annotations

import shutil

from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl

from rnpkill.ui.navigation import NavigationState
from rnpkill.ui.renderer import MenuRenderer


class LayoutBuilder:
    """Ensambla el layout completo del menú."""

    def __init__(self, renderer: MenuRenderer, banner_lines: int) -> None:
        self._renderer = renderer
        self._banner_lines = banner_lines
        self._compact = False
        self._banner_effective_lines = banner_lines
        self._visible_rows = 15

    # ------------------------------------------------------------------ #
    # Cálculo de tamaños
    # ------------------------------------------------------------------ #
    def recalculate(self) -> None:
        """Recalcula visibilidad y modo compacto según la terminal."""
        size = shutil.get_terminal_size(fallback=(80, 24))
        terminal_lines = size.lines
        terminal_cols = size.columns

        self._compact = terminal_lines < 15 or terminal_cols < 60
        self._renderer.set_compact(self._compact)

        self._banner_effective_lines = 1 if self._compact else self._banner_lines
        summary_lines = self._renderer.summary_height

        reserved = self._banner_effective_lines + summary_lines + 2
        self._visible_rows = max(3, terminal_lines - reserved)

    @property
    def visible_rows(self) -> int:
        return self._visible_rows

    @property
    def compact(self) -> bool:
        return self._compact

    # ------------------------------------------------------------------ #
    # Construcción
    # ------------------------------------------------------------------ #
    def build(self, state: NavigationState) -> Layout:
        """Construye el Layout completo."""

        banner_window = Window(
            FormattedTextControl(text=self._renderer.banner_text),
            height=self._banner_effective_lines,
            dont_extend_height=True,
        )

        summary_window = Window(
            FormattedTextControl(text=self._renderer.summary_text),
            height=self._renderer.summary_height,
            dont_extend_height=True,
        )

        list_window = Window(
            FormattedTextControl(
                text=lambda: self._renderer.rows_text(state, self._visible_rows),
                show_cursor=False,
            ),
            dont_extend_height=True,
        )

        help_window = Window(
            FormattedTextControl(text=lambda: self._renderer.help_text(state)),
            height=1,
            dont_extend_height=True,
        )

        return Layout(
            HSplit([banner_window, summary_window, list_window, help_window]),
            focused_element=list_window,
        )