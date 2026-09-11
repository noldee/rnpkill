"""Eliminación quirúrgica de directorios con manejo de errores."""
from __future__ import annotations

import os
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(slots=True)
class DeleteResult:
    """Resultado de un intento de eliminación."""

    path: Path
    success: bool
    freed_bytes: int = 0
    error: str | None = None


class DirectoryDeleter:
    """Elimina directorios preservando el resto del proyecto.

    Aplica un ``onerror`` handler que resuelve los típicos errores de
    permisos en Windows (archivos de solo lectura) y en Linux (modo
    0o444 en cachés de npm/pip).
    """

    def delete(self, path: Path, known_size: int = 0) -> DeleteResult:
        """Elimina ``path`` recursivamente.

        Args:
            path: Directorio a eliminar.
            known_size: Tamaño precalculado para reportar bytes liberados.

        Returns:
            :class:`DeleteResult` con el estado del intento.
        """
        if not path.exists():
            return DeleteResult(path=path, success=False, error="La ruta no existe")

        try:
            shutil.rmtree(path, onerror=self._handle_rm_error)
            return DeleteResult(path=path, success=True, freed_bytes=known_size)
        except Exception as exc:  # noqa: BLE001 — queremos capturar cualquier fallo
            return DeleteResult(path=path, success=False, error=str(exc))

    @staticmethod
    def _handle_rm_error(
        func: Callable[[str], None],
        target: str,
        exc_info: tuple[type[BaseException], BaseException, object],
    ) -> None:
        """Resuelve errores de permisos y reintenta la operación."""
        try:
            os.chmod(target, stat.S_IWRITE | stat.S_IREAD)
            func(target)
        except Exception:
            raise exc_info[1]