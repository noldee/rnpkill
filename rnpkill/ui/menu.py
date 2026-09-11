"""Menú interactivo: árbol plegable, temas y búsqueda incremental."""
from __future__ import annotations

import shutil
import time
from collections import defaultdict
from typing import Sequence

from prompt_toolkit import Application
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl

from rnpkill.core.models import TargetFolder
from rnpkill.utils.formatters import format_bytes
from rnpkill.utils.themes import ColorPalette, get_theme, to_prompt_style

_HELP_TEXT = (
    " ↑/↓ mover · ←/→ plegar · espacio marcar · a todo · s/n/d ordenar "
    "· / buscar · enter confirmar · q salir"
)

_ORDERS = ("size", "name", "date", "path")


class TargetMenu:
    """Menú con árbol plegable, temas y búsqueda incremental."""

    def __init__(self, banner_ascii: str, theme: str = "default") -> None:
        self._banner = banner_ascii.rstrip("\n")
        self._banner_lines = self._banner.count("\n") + 1
        self._palette: ColorPalette = get_theme(theme)

        self._all_targets: list[TargetFolder] = []
        self._grouped: dict[str, list[TargetFolder]] = {}
        self._project_order: list[str] = []
        self._collapsed: set[str] = set()
        self._selected_paths: set[str] = set()

        # Lista visible (rows navegables) y cursor
        self._rows: list[tuple[str, TargetFolder | None]] = []
        self._cursor: int = 0
        self._visible: int = 15

        self._summary: str = ""
        self._result: list[TargetFolder] = []
        self._order: str = "size"
        self._search: str = ""
        self._search_mode: bool = False

    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #
    def select(
        self,
        targets: Sequence[TargetFolder],
        summary: str = "",
        order: str = "size",
    ) -> list[TargetFolder]:
        """Muestra el menú y devuelve las carpetas marcadas."""
        self._all_targets = list(targets)
        self._summary = summary
        self._order = order if order in _ORDERS else "size"
        self._search = ""
        self._search_mode = False
        self._collapsed = set()
        self._selected_paths = set()
        self._result = []
        self._cursor = 0
        self._regroup()
        self._visible = self._compute_visible_rows()

        app = Application(
            layout=self._build_layout(),
            key_bindings=self._build_keybindings(),
            style=to_prompt_style(self._palette),
            full_screen=False,
        )
        app.run()
        return self._result

    # ------------------------------------------------------------------ #
    # Agrupación / orden
    # ------------------------------------------------------------------ #
    def _regroup(self) -> None:
        """Reagrupa y reordena las carpetas visibles."""
        filtered = [
            t
            for t in self._all_targets
            if not self._search
            or self._search.lower() in str(t.path).lower()
        ]

        self._grouped = defaultdict(list)
        for target in filtered:
            self._grouped[str(target.path.parent)].append(target)

        for group in self._grouped.values():
            group.sort(key=self._sort_key)

        self._project_order = sorted(
            self._grouped.keys(), key=self._project_sort_key
        )

        self._rebuild_rows()

    def _sort_key(self, t: TargetFolder):
        if self._order == "size":
            return -t.size_bytes
        if self._order == "name":
            return t.name.lower()
        if self._order == "date":
            return -t.mtime
        return str(t.path).lower()

    def _project_sort_key(self, path_str: str):
        if self._order == "size":
            return -sum(t.size_bytes for t in self._grouped[path_str])
        if self._order == "date":
            return -max(t.mtime for t in self._grouped[path_str])
        return path_str.lower()

    def _rebuild_rows(self) -> None:
        """Reconstruye la lista de filas navegables (proyectos + hijos)."""
        rows: list[tuple[str, TargetFolder | None]] = []
        for proj in self._project_order:
            rows.append(("project", None))
            if proj not in self._collapsed:
                for target in self._grouped[proj]:
                    rows.append(("target", target))
        self._rows = rows
        self._cursor = min(self._cursor, max(0, len(rows) - 1))

    # ------------------------------------------------------------------ #
    # Layout
    # ------------------------------------------------------------------ #
    def _compute_visible_rows(self) -> int:
        terminal_lines = shutil.get_terminal_size(fallback=(80, 24)).lines
        reserved = self._banner_lines + 5
        available = max(5, terminal_lines - reserved)
        return min(len(self._rows), available)

    def _build_layout(self) -> Layout:
        banner_window = Window(
            FormattedTextControl(
                text=FormattedText([("class:banner", self._banner)])
            ),
            height=self._banner_lines,
            dont_extend_height=True,
        )
        summary_window = Window(
            FormattedTextControl(
                text=FormattedText([("class:summary", f" {self._summary}")])
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
            FormattedTextControl(text=self._render_help),
            height=1,
            dont_extend_height=True,
        )
        return Layout(
            HSplit([banner_window, summary_window, list_window, help_window])
        )

    # ------------------------------------------------------------------ #
    # Render
    # ------------------------------------------------------------------ #
    def _render_rows(self) -> FormattedText:
        if not self._rows:
            return FormattedText([("class:dim", " (sin resultados)\n")])

        n = len(self._rows)
        half = self._visible // 2
        start = max(0, min(self._cursor - half, n - self._visible))
        end = min(n, start + self._visible)

        fragments: list[tuple[str, str]] = []
        if start > 0:
            fragments.append(("class:dim", f"  ↑ {start} más arriba…\n"))

        for i in range(start, end):
            kind, target = self._rows[i]
            is_cursor = i == self._cursor
            if kind == "project":
                proj = self._project_order[self._project_index(i)]
                arrow = "▶" if proj in self._collapsed else "▼"
                path = target.path.parent if target else None
                label = proj.replace(str(targets_root()), "~") if target else proj
                fragments.append(
                    (
                        "class:selected" if is_cursor else "class:tree",
                        f" {arrow} {label}\n",
                    )
                )
            else:
                assert target is not None
                check = "X" if str(target.path) in self._selected_paths else " "
                pointer = "❯" if is_cursor else " "
                size = format_bytes(target.size_bytes)
                age = _human_age(target.mtime)
                style = "class:selected" if is_cursor else ""
                fragments.append(
                    (
                        style,
                        f"   {pointer} [{check}] {size:>10}  {age:>8}  {target.name}\n",
                    )
                )

        remaining = n - end
        if remaining > 0:
            fragments.append(("class:dim", f"  ↓ {remaining} más abajo…\n"))
        return FormattedText(fragments)

    def _project_index(self, row_index: int) -> int:
        """Índice de proyecto en ``_project_order`` para una fila dada."""
        seen = -1
        for i, (kind, _) in enumerate(self._rows[: row_index + 1]):
            if kind == "project":
                seen += 1
        return max(0, seen)

    def _render_help(self) -> FormattedText:
        if self._search_mode:
            return FormattedText(
                [
                    ("class:help", " 🔍 "),
                    ("class:summary", self._search),
                    ("class:help", "█  "),
                    ("class:dim", "(enter aplicar · esc cancelar)"),
                ]
            )
        order_hint = f" [orden: {self._order}]"
        return FormattedText([("class:help", _HELP_TEXT + order_hint)])

    # ------------------------------------------------------------------ #
    # Keybindings
    # ------------------------------------------------------------------ #
    def _build_keybindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("up")
        @kb.add("k")
        def _up(event) -> None:
            self._move(-1)

        @kb.add("down")
        @kb.add("j")
        def _down(event) -> None:
            self._move(+1)

        @kb.add("left")
        @kb.add("h")
        def _collapse(event) -> None:
            self._collapse_current()

        @kb.add("right")
        @kb.add("l")
        def _expand(event) -> None:
            self._expand_current()

        @kb.add("space")
        def _toggle(event) -> None:
            kind, target = self._rows[self._cursor]
            if kind == "project":
                # Toggle todo el proyecto
                proj = self._project_order[self._project_index(self._cursor)]
                children = self._grouped[proj]
                paths = {str(t.path) for t in children}
                if paths.issubset(self._selected_paths):
                    self._selected_paths -= paths
                else:
                    self._selected_paths |= paths
            elif target is not None:
                p = str(target.path)
                if p in self._selected_paths:
                    self._selected_paths.discard(p)
                else:
                    self._selected_paths.add(p)

        @kb.add("a")
        def _all(event) -> None:
            visible = {str(t.path) for t in self._all_targets}
            if visible.issubset(self._selected_paths):
                self._selected_paths.clear()
            else:
                self._selected_paths = set(visible)

        @kb.add("s")
        def _order_size(event) -> None:
            self._order = "size"
            self._regroup()

        @kb.add("n")
        def _order_name(event) -> None:
            self._order = "name"
            self._regroup()

        @kb.add("d")
        def _order_date(event) -> None:
            self._order = "date"
            self._regroup()

        @kb.add("p")
        def _order_path(event) -> None:
            self._order = "path"
            self._regroup()

        @kb.add("/")
        def _start_search(event) -> None:
            self._search_mode = True
            self._search = ""

        @kb.add("enter", eager=True)
        def _confirm(event) -> None:
            if self._search_mode:
                self._search_mode = False
                self._regroup()
                return
            self._result = [
                t
                for t in self._all_targets
                if str(t.path) in self._selected_paths
            ]
            event.app.exit()

        @kb.add("escape", eager=True)
        def _escape(event) -> None:
            if self._search_mode:
                self._search_mode = False
                self._search = ""
                self._regroup()
            else:
                self._result = []
                event.app.exit()

        @kb.add("c-c")
        def _abort(event) -> None:
            self._result = []
            event.app.exit()

        @kb.add("q")
        def _quit(event) -> None:
            if self._search_mode:
                self._search += "q"
                self._regroup()
            else:
                self._result = []
                event.app.exit()

        @kb.add("<any>")
        def _any(event) -> None:
            if self._search_mode:
                data = event.data or ""
                if data.isprintable():
                    self._search += data
                    self._regroup()

        @kb.add("backspace")
        def _backspace(event) -> None:
            if self._search_mode and self._search:
                self._search = self._search[:-1]
                self._regroup()

        return kb

    # ------------------------------------------------------------------ #
    # Navegación
    # ------------------------------------------------------------------ #
    def _move(self, delta: int) -> None:
        if not self._rows:
            return
        self._cursor = max(0, min(len(self._rows) - 1, self._cursor + delta))

    def _current_project(self) -> str | None:
        if not self._rows:
            return None
        kind, _ = self._rows[self._cursor]
        if kind == "project":
            return self._project_order[self._project_index(self._cursor)]
        # Buscar hacia atrás el proyecto padre
        for i in range(self._cursor, -1, -1):
            if self._rows[i][0] == "project":
                return self._project_order[self._project_index(i)]
        return None

    def _collapse_current(self) -> None:
        proj = self._current_project()
        if proj:
            self._collapsed.add(proj)
            self._rebuild_rows()

    def _expand_current(self) -> None:
        proj = self._current_project()
        if proj:
            self._collapsed.discard(proj)
            self._rebuild_rows()


# ---------------------------------------------------------------------- #
# Helpers
# ---------------------------------------------------------------------- #
def targets_root():
    """Raíz usada para acortar rutas en el árbol (heurística simple)."""
    from pathlib import Path
    return Path.home()


def _human_age(mtime: float) -> str:
    """Convierte un timestamp en texto tipo ``3m``, ``2d``, ``1y``."""
    if mtime <= 0:
        return "?"
    delta = time.time() - mtime
    if delta < 3600:
        return f"{int(delta // 60)}m"
    if delta < 86400:
        return f"{int(delta // 3600)}h"
    if delta < 2592000:
        return f"{int(delta // 86400)}d"
    if delta < 31536000:
        return f"{int(delta // 2592000)}mo"
    return f"{int(delta // 31536000)}y"