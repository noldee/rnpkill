"""Menú interactivo con prompt_toolkit — banner fijo y scroll interno.

Sustituye a ``questionary`` para resolver el problema de que el banner
ASCII desaparecía al navegar con las flechas: ``questionary`` imprime
en modo *inline* y cuando la lista supera el alto del terminal, el
scroll empuja el banner fuera de la pantalla.

Aquí construimos una ``Application`` de ``prompt_toolkit`` con un
layout de 3 zonas —banner fijo, lista con scroll interno, ayuda— para
que todo permanezca visible sin importar cuántos ítems haya.
"""
from __future__ import annotations

import shutil
from typing import Sequence

from prompt_toolkit import Application
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style

from rnpkill.core.models import TargetFolder
from rnpkill.utils.formatters import format_bytes


_STYLE = Style.from_dict(
    {
        "banner": "bold cyan",
        "summary": "bold green",
        "selected": "reverse bold",
        "dim": "ansibrightblack",
        "help": "bg:#222222 #cccccc",
    }
)

_HELP_TEXT = (
    " ↑/↓ mover · espacio marcar · a (todo) · enter confirmar · q salir"
)


class TargetMenu:
    """Checkbox interactivo con banner fijo y scroll interno."""

    def __init__(self, banner_ascii: str) -> None:
        """Inicializa el menú.

        Args:
            banner_ascii: Arte ASCII a mostrar fijo en la parte superior.
        """
        self._banner = banner_ascii.rstrip("\n")
        self._banner_lines = self._banner.count("\n") + 1
        self._summary: str = ""
        self._targets: list[TargetFolder] = []
        self._selected: set[int] = set()
        self._cursor: int = 0
        self._visible: int = 15
        self._result: list[TargetFolder] = []
    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #
    def select(
        self,
        targets: Sequence[TargetFolder],
        summary: str = "",
    ) -> list[TargetFolder]:
        """Presenta el menú y devuelve las carpetas marcadas.

        Args:
            targets: Lista de carpetas a mostrar.
            summary: Línea resumen que se mostrará bajo el banner.

        Returns:
            Carpetas seleccionadas (vacía si se cancela con ``q``/``Esc``).
        """
        self._targets = list(targets)
        self._summary = summary
        self._selected = set()
        self._cursor = 0
        self._result = []
        self._visible = self._compute_visible_rows()

        app = Application(
            layout=self._build_layout(),
            key_bindings=self._build_keybindings(),
            style=_STYLE,
            full_screen=False,
        )
        app.run()
        return self._result
    # ------------------------------------------------------------------ #
    # Cálculo de filas visibles
    # ------------------------------------------------------------------ #
    def _compute_visible_rows(self) -> int:
        """Cuántos ítems caben sin que el terminal haga scroll."""
        terminal_lines = shutil.get_terminal_size(fallback=(80, 24)).lines
        # banner + summary + margen + ayuda
        reserved = self._banner_lines + 4
        available = max(5, terminal_lines - reserved)
        return min(len(self._targets), available)

    # ------------------------------------------------------------------ #
    # Layout
    # ------------------------------------------------------------------ #
    def _build_layout(self) -> Layout:
        banner_window = Window(
            FormattedTextControl(
                text=FormattedText([("class:banner", self._banner)]),
            ),
            height=self._banner_lines,
            dont_extend_height=True,
        )
        summary_window = Window(
            FormattedTextControl(
                text=FormattedText([("class:summary", f" {self._summary}")]),
            ),
            height=1,
            dont_extend_height=True,
        )
        list_window = Window(
            FormattedTextControl(text=self._render_rows, show_cursor=False),
            height=self._visible,
            dont_extend_height=True,
        )
        help_window = Window(
            FormattedTextControl(
                text=FormattedText([("class:help", _HELP_TEXT)]),
            ),
            height=1,
            dont_extend_height=True,
        )
        return Layout(
            HSplit([banner_window, summary_window, list_window, help_window])
        )

    # ------------------------------------------------------------------ #
    # Render de la lista
    # ------------------------------------------------------------------ #
    def _render_rows(self) -> FormattedText:
        """Construye las líneas visibles con ventana deslizante."""
        n = len(self._targets)
        half = self._visible // 2

        # Ventana que sigue al cursor, siempre dentro de [0, n-visible].
        start = max(0, min(self._cursor - half, n - self._visible))
        end = start + self._visible

        fragments: list[tuple[str, str]] = []

        if start > 0:
            fragments.append(("class:dim", f"  ↑ {start} más arriba…\n"))

        for i in range(start, end):
            target = self._targets[i]
            check = "X" if i in self._selected else " "
            pointer = "❯" if i == self._cursor else " "
            size = format_bytes(target.size_bytes)
            style = "class:selected" if i == self._cursor else ""
            fragments.append(
                (
                    style,
                    f" {pointer} [{check}] {size:>10}   {target.display_name}\n",
                )
            )

        remaining = n - end
        if remaining > 0:
            fragments.append(("class:dim", f"  ↓ {remaining} más abajo…\n"))

        return FormattedText(fragments)

    # ------------------------------------------------------------------ #
    # Keybindings
    # ------------------------------------------------------------------ #
    def _build_keybindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("up")
        @kb.add("k")
        def _move_up(event) -> None:
            if self._cursor > 0:
                self._cursor -= 1

        @kb.add("down")
        @kb.add("j")
        def _move_down(event) -> None:
            if self._cursor < len(self._targets) - 1:
                self._cursor += 1

        @kb.add("space")
        def _toggle(event) -> None:
            if self._cursor in self._selected:
                self._selected.discard(self._cursor)
            else:
                self._selected.add(self._cursor)

        @kb.add("a")
        def _toggle_all(event) -> None:
            if len(self._selected) == len(self._targets):
                self._selected.clear()
            else:
                self._selected = set(range(len(self._targets)))

        @kb.add("enter")
        def _confirm(event) -> None:
            self._result = [self._targets[i] for i in sorted(self._selected)]
            event.app.exit()

        @kb.add("c-c")
        @kb.add("q")
        @kb.add("escape")
        def _abort(event) -> None:
            self._result = []
            event.app.exit()

        return kb