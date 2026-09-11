"""Estado de navegación del menú: agrupación, orden, cursor, selección.

Este módulo NO conoce prompt_toolkit. Solo contiene la lógica de "qué
se ve, en qué orden, con qué cursor". Es 100% testeable sin UI.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Sequence

from rnpkill.core.models import TargetFolder

ORDERS = ("size", "name", "date", "path")

RowKind = str  # "project" | "target"
Row = tuple[RowKind, TargetFolder | None]


class NavigationState:
    """Encapsula el estado navegable del menú."""

    def __init__(self) -> None:
        self.all_targets: list[TargetFolder] = []
        self.grouped: dict[str, list[TargetFolder]] = {}
        self.project_order: list[str] = []
        self.collapsed: set[str] = set()
        self.selected_paths: set[str] = set()
        self.rows: list[Row] = []
        self.cursor: int = 0
        self.order: str = "size"
        self.search: str = ""
        self.search_mode: bool = False

    # ------------------------------------------------------------------ #
    # Inicialización
    # ------------------------------------------------------------------ #
    def load(self, targets: Sequence[TargetFolder]) -> None:
        """Carga las carpetas y resetea el estado."""
        self.all_targets = list(targets)
        self.collapsed = set()
        self.selected_paths = set()
        self.search = ""
        self.search_mode = False
        self.cursor = 0
        self.regroup()

    # ------------------------------------------------------------------ #
    # Agrupación / orden
    # ------------------------------------------------------------------ #
    def regroup(self) -> None:
        """Reagrupa y reordena según el filtro de búsqueda activo."""
        filtered = [
            t for t in self.all_targets
            if not self.search or self.search.lower() in str(t.path).lower()
        ]
        self.grouped = defaultdict(list)
        for target in filtered:
            self.grouped[str(target.path.parent)].append(target)
        for group in self.grouped.values():
            group.sort(key=self._sort_key)
        self.project_order = sorted(
            self.grouped.keys(), key=self._project_sort_key
        )
        self.rebuild_rows()

    def _sort_key(self, t: TargetFolder):
        if self.order == "size":
            return -t.size_bytes
        if self.order == "name":
            return t.name.lower()
        if self.order == "date":
            return -t.mtime
        return str(t.path).lower()

    def _project_sort_key(self, path_str: str):
        if self.order == "size":
            return -sum(t.size_bytes for t in self.grouped[path_str])
        if self.order == "date":
            return -max(t.mtime for t in self.grouped[path_str])
        return path_str.lower()

    def rebuild_rows(self) -> None:
        """Reconstruye la lista de filas visibles (proyectos + hijos)."""
        rows: list[Row] = []
        for proj in self.project_order:
            rows.append(("project", None))
            if proj not in self.collapsed:
                for target in self.grouped[proj]:
                    rows.append(("target", target))
        self.rows = rows
        self.cursor = min(self.cursor, max(0, len(rows) - 1))

    # ------------------------------------------------------------------ #
    # Navegación
    # ------------------------------------------------------------------ #
    def move(self, delta: int) -> None:
        if not self.rows:
            return
        self.cursor = max(0, min(len(self.rows) - 1, self.cursor + delta))

    def project_index_at(self, row_index: int) -> int:
        """Índice del proyecto en ``project_order`` para una fila dada."""
        seen = -1
        for i, (kind, _) in enumerate(self.rows[: row_index + 1]):
            if kind == "project":
                seen += 1
        return max(0, seen)

    def current_project(self) -> str | None:
        """Proyecto del cursor actual (o del ancestro más cercano)."""
        if not self.rows:
            return None
        kind, _ = self.rows[self.cursor]
        if kind == "project":
            return self.project_order[self.project_index_at(self.cursor)]
        for i in range(self.cursor, -1, -1):
            if self.rows[i][0] == "project":
                return self.project_order[self.project_index_at(i)]
        return None

    def collapse_current(self) -> None:
        proj = self.current_project()
        if proj:
            self.collapsed.add(proj)
            self.rebuild_rows()

    def expand_current(self) -> None:
        proj = self.current_project()
        if proj:
            self.collapsed.discard(proj)
            self.rebuild_rows()

    # ------------------------------------------------------------------ #
    # Selección
    # ------------------------------------------------------------------ #
    def toggle_current(self) -> None:
        """Marca/desmarca fila actual. En proyecto, marca todos sus hijos."""
        kind, target = self.rows[self.cursor]
        if kind == "project":
            proj = self.project_order[self.project_index_at(self.cursor)]
            paths = {str(t.path) for t in self.grouped[proj]}
            if paths.issubset(self.selected_paths):
                self.selected_paths -= paths
            else:
                self.selected_paths |= paths
        elif target is not None:
            p = str(target.path)
            if p in self.selected_paths:
                self.selected_paths.discard(p)
            else:
                self.selected_paths.add(p)

    def toggle_all(self) -> None:
        visible = {str(t.path) for t in self.all_targets}
        if visible.issubset(self.selected_paths):
            self.selected_paths.clear()
        else:
            self.selected_paths = set(visible)

    def selected_targets(self) -> list[TargetFolder]:
        return [
            t for t in self.all_targets
            if str(t.path) in self.selected_paths
        ]

    # ------------------------------------------------------------------ #
    # Búsqueda
    # ------------------------------------------------------------------ #
    def start_search(self) -> None:
        self.search_mode = True
        self.search = ""

    def update_search(self, char: str) -> None:
        self.search += char
        self.regroup()

    def delete_search_char(self) -> None:
        if self.search:
            self.search = self.search[:-1]
            self.regroup()

    def cancel_search(self) -> None:
        self.search_mode = False
        self.search = ""
        self.regroup()

    def commit_search(self) -> None:
        self.search_mode = False
        self.regroup()

    # ------------------------------------------------------------------ #
    # Orden
    # ------------------------------------------------------------------ #
    def set_order(self, order: str) -> None:
        if order in ORDERS:
            self.order = order
            self.regroup()