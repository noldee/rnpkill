"""Menú interactivo — orquestador delgado.

Une NavigationState + LayoutBuilder + MenuRenderer + KeyBindings.
La lógica real vive en los módulos vecinos; aquí solo se compone todo.
"""
from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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

    def __init__(
        self,
        banner_ascii: str,
        theme: str = "default",
        deleter=None,
    ) -> None:
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
        self._deleter = deleter
        self._app: Application | None = None

    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #
    def select(
        self,
        targets: Sequence[TargetFolder],
        total_bytes: int = 0,
        scan_seconds: float = 0.0,
        order: str = "size",
        measurer=None,
    ) -> list[TargetFolder]:
        """Muestra el menú y devuelve las carpetas marcadas.

        Args:
            targets: Carpetas a mostrar.
            total_bytes: Total de bytes ya medidos.
            scan_seconds: Tiempo del escaneo inicial.
            order: Orden inicial (size/name/date/path).
            measurer: Callable opcional ``(state, on_update)`` para
                medir tamaños en background.

        Returns:
            Carpetas seleccionadas (vacía si se cancela con q/Esc/Ctrl+C).
        """
        self._state.load(targets)
        self._state.set_order(order)
        self._state.mark_all_measuring()

        self._renderer = MenuRenderer(
            banner=self._banner,
            summary_left=f"{len(targets)} carpeta(s)",
            summary_right="midiendo…",
            compact_mode=False,
        )
        self._layout_builder = LayoutBuilder(self._renderer, self._banner_lines)
        self._layout_builder.recalculate()

        self._result = []
        self._total_bytes_seen = total_bytes

        self._app = Application(
            layout=self._layout_builder.build(self._state),
            key_bindings=build_keybindings(
                self._state,
                self._on_confirm,
                on_delete=self._on_delete,
            ),
            style=to_prompt_style(self._palette),
            full_screen=True,
            mouse_support=False,
        )

        if measurer is not None:
            self._start_measurer(measurer, total_bytes)

        self._app.run()
        return self._result

    # ------------------------------------------------------------------ #
    # Medición en background
    # ------------------------------------------------------------------ #
    def _start_measurer(self, measurer, total_bytes: int) -> None:
        """Lanza la medición de tamaños en background."""

        def _on_update(path: str, size: int, error: str | None = None) -> None:
            self._state.apply_size_update(path, size, error)
            if size > 0:
                self._total_bytes_seen += size
            self._renderer = MenuRenderer(
                banner=self._banner,
                summary_left=(
                    f"{len(self._state.all_targets)} carpeta(s) · "
                    f"{format_bytes(self._total_bytes_seen)}"
                ),
                summary_right=self._progress_label(),
                compact_mode=self._layout_builder.compact,
            )
            self._layout_builder._renderer = self._renderer
            if self._app:
                self._app.invalidate()

        measurer(self._state, _on_update)

    def _progress_label(self) -> str:
        """Etiqueta de progreso: 'midiendo 42/114' o 'listo'."""
        total = len(self._state.all_targets)
        done = sum(1 for t in self._state.all_targets if not t.measuring)
        if done < total:
            return f"midiendo {done}/{total}"
        return "listo"

    # ------------------------------------------------------------------ #
    # Callbacks
    # ------------------------------------------------------------------ #
    def _on_confirm(self, event, abort: bool = False) -> None:
        """Se dispara con q, Esc o Ctrl+C."""
        if abort:
            self._result = []
        else:
            # Devolver TODAS las carpetas que ya se borraron (done o error)
            self._result = [
                t for t in self._state.all_targets
                if t.is_deleted or t.has_delete_error
            ]
        event.app.exit()

    def _on_delete(self, selected: list[TargetFolder], event) -> None:
        """Se llama al presionar Enter con carpetas marcadas.

        Borra las carpetas en background, actualiza el estado por fila,
        y **NO sale del menú**. Al terminar cada borrado exitoso, la fila
        se elimina del árbol. El usuario sale con `q` cuando quiera.
        """
        if self._deleter is None:
            # Sin deleter configurado → no hacemos nada
            return

        def _worker() -> None:
            # 1. Marcar todas como 'deleting'
            for t in selected:
                self._state.mark_deleting(str(t.path))
            if self._app:
                self._app.invalidate()

            # 2. Borrar en paralelo
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(
                        self._deleter.delete, t.path, t.size_bytes
                    ): t
                    for t in selected
                }
                for future in as_completed(futures):
                    target = futures[future]
                    try:
                        result = future.result()
                        if result.success:
                            self._state.mark_deleted(str(target.path))
                        else:
                            self._state.mark_deleted(
                                str(target.path), error=result.error
                            )
                    except Exception as exc:  # noqa: BLE001
                        self._state.mark_deleted(
                            str(target.path), error=str(exc)
                        )
                    if self._app:
                        self._app.invalidate()

            # 3. Pequeña pausa para que se vea el ✓ antes de quitar las filas
            time.sleep(0.8)

            # 4. Quitar las borradas con éxito del árbol (mantener las que fallaron)
            for t in list(selected):
                if t.is_deleted:
                    self._state.remove_deleted(str(t.path))

            if self._app:
                self._app.invalidate()

            # 5. NO se llama a event.app.exit() → el menú sigue abierto

        threading.Thread(target=_worker, daemon=True).start()