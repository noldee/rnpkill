"""Renderizado de texto para el menú (banner, summary, filas, help).

Aquí vive todo lo que convierte estado → FormattedText de prompt_toolkit.
Cero lógica de navegación, cero construcción de widgets.
"""
from __future__ import annotations

import time

from prompt_toolkit.formatted_text import FormattedText

from rnpkill.core.models import TargetFolder
from rnpkill.utils.formatters import format_bytes
from rnpkill.ui.navigation import NavigationState

HELP_TEXT = (
    " ↑/↓ mover · ←/→ plegar · espacio marcar · a todo · "
    "s/n/d ordenar · / buscar · enter confirmar · q salir"
)


class MenuRenderer:
    """Convierte el estado del menú en texto formateado."""

    def __init__(
        self,
        banner: str,
        summary_left: str,
        summary_right: str,
        compact_mode: bool,
    ) -> None:
        self._banner = banner
        self._summary_left = summary_left
        self._summary_right = summary_right
        self._compact = compact_mode

    def set_compact(self, compact: bool) -> None:
        self._compact = compact

    # ------------------------------------------------------------------ #
    # Banner
    # ------------------------------------------------------------------ #
    def banner_text(self) -> FormattedText:
        if self._compact:
            return FormattedText([("class:banner", " 🧹 rnpkill")])
        return FormattedText([("class:banner", self._banner)])

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    def summary_text(self) -> FormattedText:
        if self._compact:
            line = f" {self._summary_left} · {self._summary_right}"
            return FormattedText([("class:summary", line)])
        return FormattedText(
            [
                ("class:summary", f" {self._summary_left}\n"),
                ("class:dim", f" {self._summary_right}"),
            ]
        )

    @property
    def summary_height(self) -> int:
        return 1 if self._compact else 2

    # ------------------------------------------------------------------ #
    # Filas
    # ------------------------------------------------------------------ #
    def rows_text(self, state: NavigationState, visible: int) -> FormattedText:
        rows = state.rows
        if not rows:
            return FormattedText([("class:dim", " (sin resultados)\n")])

        n = len(rows)
        half = visible // 2
        start = max(0, min(state.cursor - half, n - visible))
        end = min(n, start + visible)

        fragments: list[tuple[str, str]] = []

        if start > 0:
            fragments.append(("class:dim", f"  ↑ {start} más arriba…\n"))

        for i in range(start, end):
            kind, target = rows[i]
            is_cursor = i == state.cursor
            if kind == "project":
                proj = state.project_order[state.project_index_at(i)]
                arrow = "▶" if proj in state.collapsed else "▼"
                fragments.append(
                    (
                        "class:selected" if is_cursor else "class:tree",
                        f" {arrow} {proj}\n",
                    )
                )
            else:
                fragments.append(
                    self._render_target_row(target, is_cursor, state)
                )

        remaining = n - end
        if remaining > 0:
            fragments.append(("class:dim", f"  ↓ {remaining} más abajo…\n"))
        return FormattedText(fragments)

    def _render_target_row(
        self,
        target: TargetFolder | None,
        is_cursor: bool,
        state: NavigationState,
    ) -> tuple[str, str]:
        assert target is not None
        check = "X" if str(target.path) in state.selected_paths else " "
        pointer = "❯" if is_cursor else " "
        size = format_bytes(target.size_bytes)
        age = human_age(target.mtime)

        # ─── Prefijo de estado de borrado ────────────────────────
        if target.is_deleting:
            prefix = "[DELETING...]"
            style = "class:deleting"
        elif target.is_deleted:
            prefix = "[DELETE ✓  ]"
            style = "class:deleted"
        elif target.has_delete_error:
            prefix = "[DELETE ✗  ]"
            style = "class:delete-error"
        else:
            prefix = "            "  # 12 espacios para alinear
            style = "class:selected" if is_cursor else ""

        return (
            style,
            f" {prefix} {pointer} [{check}] {size:>10}  {age:>8}  {target.name}\n",
        )

    # ------------------------------------------------------------------ #
    # Help
    # ------------------------------------------------------------------ #
    def help_text(self, state: NavigationState) -> FormattedText:
        if state.search_mode:
            return FormattedText(
                [
                    ("class:help", " 🔍 "),
                    ("class:summary", state.search),
                    ("class:help", "█  "),
                    ("class:dim", "(enter aplicar · esc cancelar)"),
                ]
            )

        if any(t.is_deleting for t in state.all_targets):
            return FormattedText(
                [("class:deleting", " ⏳ Borrando carpetas seleccionadas…")]
            )

        # Nuevo: cuando hay algo ya borrado en la sesión
        if any(t.is_deleted for t in state.all_targets):
            return FormattedText(
                [("class:deleted", " ✓ Listo · sigue marcando o pulsa q para salir")]
            )

        return FormattedText(
            [("class:help", HELP_TEXT + f" [orden: {state.order}]")]
        )


# ---------------------------------------------------------------------- #
# Helpers
# ---------------------------------------------------------------------- #
def human_age(mtime: float) -> str:
    """Convierte un timestamp en texto corto: ``3m``, ``2d``, ``1y``."""
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