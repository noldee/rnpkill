"""Cálculo de tamaños de directorios — versión de alto rendimiento.

Estrategia escalonada:
    1. Linux/macOS: usa ``du -sb`` (C nativo, ~50–100x más rápido).
    2. Fallback (Windows / du no disponible): walk paralelo con
       ``ThreadPoolExecutor`` (I/O bound → el GIL no bloquea).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


class SizeCalculator:
    """Mide directorios minimizando syscalls y aprovechando concurrencia."""

    def __init__(self, max_workers: int | None = None) -> None:
        """Inicializa el calculador.

        Args:
            max_workers: Hilos para el fallback paralelo. Por defecto
                ``min(32, cpu_count * 4)`` (adecuado para I/O bound).
        """
        self._max_workers = max_workers or min(32, (os.cpu_count() or 4) * 4)
        # du no existe en Windows por defecto.
        self._du_path: str | None = (
            shutil.which("du") if sys.platform != "win32" else None
        )

    def calculate(self, path: Path) -> int:
        """Devuelve el tamaño de ``path`` en bytes.

        Args:
            path: Directorio a medir.

        Returns:
            Tamaño en bytes (0 si la ruta no existe o es inaccesible).
        """
        if not path.exists():
            return 0

        if self._du_path:
            size = self._du_size(path)
            if size is not None:
                return size
            # Si du falló, caemos al walk paralelo.
        return self._walk_size_parallel(path)

    # ------------------------------------------------------------------ #
    # Fast path — du nativo
    # ------------------------------------------------------------------ #
    def _du_size(self, path: Path) -> int | None:
        """Ejecuta ``du -sb`` y devuelve bytes, o ``None`` si falla.

        ``-s``: solo el total. ``-b``: tamaño aparente en bytes (no
        redondea a bloques como el ``du`` sin ``-b``, que reporta 4096
        por archivo aunque pese 100 bytes).
        """
        try:
            result = subprocess.run(
                [self._du_path, "-sb", "--", str(path)],
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (subprocess.SubprocessError, OSError):
            return None

        if result.returncode != 0 or not result.stdout:
            return None

        try:
            return int(result.stdout.split(maxsplit=1)[0])
        except (ValueError, IndexError):
            return None

    # ------------------------------------------------------------------ #
    # Fallback paralelo — Windows o cuando du falla
    # ------------------------------------------------------------------ #
    def _walk_size_parallel(self, path: Path) -> int:
        """Suma recursiva del tamaño, paralelizando subdirectorios."""
        total = 0
        subdirs: list[Path] = []

        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    try:
                        if entry.is_symlink():
                            continue  # no seguir enlaces (evita loops)
                        if entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                        elif entry.is_dir(follow_symlinks=False):
                            subdirs.append(Path(entry.path))
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            return 0

        if not subdirs:
            return total

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = [executor.submit(self._walk_size_parallel, d) for d in subdirs]
            for future in as_completed(futures):
                try:
                    total += future.result()
                except Exception:
                    # Nunca abortamos: devolvemos un límite inferior.
                    pass
        return total