"""Keybindings del menú.

Cada handler delega en NavigationState o en la Application. Cero lógica
de negocio aquí: solo "esta tecla hace esto".
"""
from __future__ import annotations

from prompt_toolkit.key_binding import KeyBindings

from rnpkill.ui.navigation import NavigationState


def build_keybindings(
    state: NavigationState,
    on_confirm: callable,
) -> KeyBindings:
    """Construye los atajos del menú.

    Args:
        state: Estado navegable que se mutará.
        on_confirm: Callback que se llama al confirmar (recibe ``event``).

    Returns:
        Un ``KeyBindings`` listo para pasar a la Application.
    """
    kb = KeyBindings()

    # ── Navegación ────────────────────────────────────────────────
    @kb.add("up")
    @kb.add("k")
    def _up(event) -> None:
        state.move(-1)

    @kb.add("down")
    @kb.add("j")
    def _down(event) -> None:
        state.move(+1)

    @kb.add("left")
    @kb.add("h")
    def _collapse(event) -> None:
        state.collapse_current()

    @kb.add("right")
    @kb.add("l")
    def _expand(event) -> None:
        state.expand_current()

    # ── Selección ─────────────────────────────────────────────────
    @kb.add("space")
    def _toggle(event) -> None:
        state.toggle_current()

    @kb.add("a")
    def _toggle_all(event) -> None:
        state.toggle_all()

    # ── Orden ─────────────────────────────────────────────────────
    @kb.add("s")
    def _order_size(event) -> None:
        state.set_order("size")

    @kb.add("n")
    def _order_name(event) -> None:
        state.set_order("name")

    @kb.add("d")
    def _order_date(event) -> None:
        state.set_order("date")

    @kb.add("p")
    def _order_path(event) -> None:
        state.set_order("path")

    # ── Búsqueda ──────────────────────────────────────────────────
    @kb.add("/")
    def _start_search(event) -> None:
        state.start_search()

    @kb.add("backspace")
    def _backspace(event) -> None:
        if state.search_mode:
            state.delete_search_char()

    @kb.add("<any>")
    def _any(event) -> None:
        if state.search_mode:
            data = event.data or ""
            if data.isprintable():
                state.update_search(data)

    # ── Confirmar / salir ─────────────────────────────────────────
    @kb.add("enter", eager=True)
    def _confirm(event) -> None:
        if state.search_mode:
            state.commit_search()
            return
        on_confirm(event)

    @kb.add("escape", eager=True)
    def _escape(event) -> None:
        if state.search_mode:
            state.cancel_search()
        else:
            on_confirm(event, abort=True)

    @kb.add("c-c")
    def _ctrl_c(event) -> None:
        on_confirm(event, abort=True)

    @kb.add("q")
    def _quit(event) -> None:
        if state.search_mode:
            state.update_search("q")
        else:
            on_confirm(event, abort=True)

    return kb