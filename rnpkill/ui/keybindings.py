"""Keybindings del menú."""
from __future__ import annotations

from prompt_toolkit.key_binding import KeyBindings

from rnpkill.ui.navigation import NavigationState


def build_keybindings(
    state: NavigationState,
    on_confirm: callable,
    on_delete: callable | None = None,
) -> KeyBindings:
    """Construye los atajos del menú.

    Args:
        state: Estado navegable que se mutará.
        on_confirm: Callback para salir (q/esc/ctrl+c).
        on_delete: Callback que recibe la lista de carpetas seleccionadas
            para borrar. Se llama al presionar Enter con algo marcado.
    """
    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def _up(event): state.move(-1)

    @kb.add("down")
    @kb.add("j")
    def _down(event): state.move(+1)

    @kb.add("left")
    @kb.add("h")
    def _collapse(event): state.collapse_current()

    @kb.add("right")
    @kb.add("l")
    def _expand(event): state.expand_current()

    @kb.add("space")
    def _toggle(event): state.toggle_current()

    @kb.add("a")
    def _toggle_all(event): state.toggle_all()

    @kb.add("s")
    def _order_size(event): state.set_order("size")

    @kb.add("n")
    def _order_name(event): state.set_order("name")

    @kb.add("d")
    def _order_date(event): state.set_order("date")

    @kb.add("p")
    def _order_path(event): state.set_order("path")

    @kb.add("/")
    def _start_search(event): state.start_search()

    @kb.add("backspace")
    def _backspace(event):
        if state.search_mode:
            state.delete_search_char()

    @kb.add("<any>")
    def _any(event):
        if state.search_mode:
            data = event.data or ""
            if data.isprintable():
                state.update_search(data)

    @kb.add("enter", eager=True)
    def _enter(event):
        """Enter: si hay algo marcado → borrar. Si no → salir."""
        if state.search_mode:
            state.commit_search()
            return

        selected = state.selected_targets()
        if not selected:
            # Nada seleccionado: salir sin borrar
            on_confirm(event, abort=True)
            return

        if on_delete is not None:
            on_delete(selected, event)
        else:
            on_confirm(event)

    @kb.add("escape", eager=True)
    def _escape(event):
        if state.search_mode:
            state.cancel_search()
        else:
            on_confirm(event, abort=True)

    @kb.add("c-c")
    def _ctrl_c(event):
        on_confirm(event, abort=True)

    @kb.add("q")
    def _quit(event):
        if state.search_mode:
            state.update_search("q")
        else:
            on_confirm(event, abort=True)

    return kb