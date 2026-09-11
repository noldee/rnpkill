"""Escaneo eficiente del sistema de archivos.

Usa ``os.walk`` con poda (pruning) para no descender dentro de las
carpetas objetivo ni de directorios irrelevantes (por ejemplo ``.git``).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Final, Iterable

from rnpkill.core.models import Project, TargetFolder

DEFAULT_TARGETS: Final[frozenset[str]] = frozenset(
    {
        # JavaScript / Node
        "node_modules",
        ".next",
        ".nuxt",
        ".parcel-cache",
        ".turbo",
        ".svelte-kit",
        # Python
        "venv",
        ".venv",
        "env",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        # Rust / Java / Go / PHP
        "target",
        ".gradle",
        ".m2",
        "vendor",
        # Bundlers genéricos
        "dist",
        "build",
    }
)

DEFAULT_EXCLUDES: Final[frozenset[str]] = frozenset(
    {
        ".git", ".hg", ".svn",
        "Library", "AppData", "Applications",
        ".cache", ".local", ".cargo", ".rustup",
        "System", "Windows", "Program Files", "Program Files (x86)",
        "$RECYCLE.BIN", ".Trash",
    }
)


class ProjectScanner:
    """Escanea un directorio raíz buscando proyectos con carpetas objetivo.

    Responsabilidad única: descubrir rutas candidatas. El cálculo del
    tamaño y la eliminación se delegan a colaboradores especializados.
    """

    def __init__(
        self,
        targets: Iterable[str] | None = None,
        excludes: Iterable[str] | None = None,
        max_depth: int | None = None,
    ) -> None:
        """Inicializa el escáner.

        Args:
            targets: Nombres de carpetas a buscar. Por defecto ``node_modules``
                y entornos virtuales comunes de Python.
            excludes: Nombres de carpetas a omitir durante el walk.
            max_depth: Profundidad máxima de recursión (``None`` = sin límite).
        """
        self._targets: frozenset[str] = frozenset(targets) if targets else DEFAULT_TARGETS
        self._excludes: frozenset[str] = frozenset(excludes) if excludes else DEFAULT_EXCLUDES
        self._max_depth = max_depth

    def scan(self, root: Path) -> list[Project]:
        """Recorre ``root`` y devuelve los proyectos con carpetas objetivo.

        Args:
            root: Directorio raíz del escaneo.

        Returns:
            Lista de :class:`Project` ordenada por ruta.

        Raises:
            ValueError: Si ``root`` no existe o no es un directorio.
        """
        if not root.exists() or not root.is_dir():
            raise ValueError(f"Ruta inválida o inexistente: {root}")

        root = root.resolve()
        projects: list[Project] = []

        for dirpath, dirnames, _ in os.walk(root, topdown=True):
            current = Path(dirpath)

            # Aplicar límite de profundidad
            if self._max_depth is not None:
                rel_parts = current.relative_to(root).parts
                if len(rel_parts) >= self._max_depth:
                    dirnames[:] = []
                    continue

            # Podar directorios excluidos (in-place para os.walk)
            dirnames[:] = [d for d in dirnames if d not in self._excludes]

            found: list[TargetFolder] = []
            for name in list(dirnames):
                if name in self._targets:
                    target_path = current / name
                    try:
                        mtime = target_path.stat().st_mtime
                    except OSError:
                        mtime = 0.0
                    found.append(
                        TargetFolder(name=name, path=target_path, mtime=mtime)
                    )
                    dirnames.remove(name)

            if found:
                projects.append(Project(path=current, targets=found))

        return sorted(projects, key=lambda p: p.path)