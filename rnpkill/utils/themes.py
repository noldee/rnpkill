"""Temas de color para la UI de rnpkill.

Inspirados en paletas populares de editores. Cada tema define estilos
tanto para ``rich`` como para ``prompt_toolkit``. Añadir un tema nuevo
es tan simple como agregar una entrada a ``THEMES``.
"""
from __future__ import annotations

from dataclasses import dataclass

from prompt_toolkit.styles import Style as PtStyle
from rich.theme import Theme as RichTheme


@dataclass(frozen=True, slots=True)
class ColorPalette:
    """Paleta de colores de un tema.

    Attributes:
        name: Identificador del tema (para --theme).
        description: Texto legible para mostrar al usuario.
        banner: Color del arte ASCII.
        summary: Color del resumen bajo el banner.
        primary: Acento principal (bordes, foco).
        success: Verde para confirmaciones.
        danger: Rojo para errores / borrado.
        dim: Texto secundario / deshabilitado.
        text: Texto base.
        help_bg: Fondo de la barra de ayuda.
        help_fg: Texto de la barra de ayuda.
    """

    name: str
    description: str
    banner: str
    summary: str
    primary: str
    success: str
    danger: str
    dim: str
    text: str
    help_bg: str
    help_fg: str


THEMES: dict[str, ColorPalette] = {
    "default": ColorPalette(
        name="default",
        description="Paleta por defecto (azul cyan)",
        banner="#56b6c2",
        summary="#98c379",
        primary="#61afef",
        success="#98c379",
        danger="#e06c75",
        dim="#7f848e",
        text="#d7dae0",
        help_bg="#222222",
        help_fg="#cccccc",
    ),
    "one-dark": ColorPalette(
        name="one-dark",
        description="One Dark Pro (Atom / VSCode)",
        banner="#61afef",
        summary="#98c379",
        primary="#61afef",
        success="#98c379",
        danger="#e06c75",
        dim="#5c6370",
        text="#abb2bf",
        help_bg="#282c34",
        help_fg="#abb2bf",
    ),
    "catppuccin": ColorPalette(
        name="catppuccin",
        description="Catppuccin Mocha (suave y pastel)",
        banner="#cba6f7",
        summary="#a6e3a1",
        primary="#89b4fa",
        success="#a6e3a1",
        danger="#f38ba8",
        dim="#6c7086",
        text="#cdd6f4",
        help_bg="#1e1e2e",
        help_fg="#cdd6f4",
    ),
    "dracula": ColorPalette(
        name="dracula",
        description="Dracula (violeta y rosa)",
        banner="#bd93f9",
        summary="#50fa7b",
        primary="#8be9fd",
        success="#50fa7b",
        danger="#ff5555",
        dim="#6272a4",
        text="#f8f8f2",
        help_bg="#282a36",
        help_fg="#f8f8f2",
    ),
    "gruvbox": ColorPalette(
        name="gruvbox",
        description="Gruvbox Dark (cálido, retro)",
        banner="#fabd2f",
        summary="#b8bb26",
        primary="#83a598",
        success="#b8bb26",
        danger="#fb4934",
        dim="#928374",
        text="#ebdbb2",
        help_bg="#3c3836",
        help_fg="#ebdbb2",
    ),
    "nord": ColorPalette(
        name="nord",
        description="Nord (frío, minimalista)",
        banner="#88c0d0",
        summary="#a3be8c",
        primary="#81a1c1",
        success="#a3be8c",
        danger="#bf616a",
        dim="#4c566a",
        text="#d8dee9",
        help_bg="#2e3440",
        help_fg="#d8dee9",
    ),
    "solarized": ColorPalette(
        name="solarized",
        description="Solarized Dark",
        banner="#268bd2",
        summary="#859900",
        primary="#2aa198",
        success="#859900",
        danger="#dc322f",
        dim="#586e75",
        text="#93a1a1",
        help_bg="#002b36",
        help_fg="#93a1a1",
    ),
}


def get_theme(name: str) -> ColorPalette:
    """Devuelve el tema por nombre, o ``default`` si no existe.

    Args:
        name: Identificador del tema.

    Returns:
        La paleta correspondiente.
    """
    return THEMES.get(name, THEMES["default"])


def list_theme_names() -> list[str]:
    """Lista de nombres disponibles para autocompletar / help."""
    return sorted(THEMES.keys())


def to_rich_theme(palette: ColorPalette) -> RichTheme:
    """Convierte la paleta a un ``rich.Theme`` para ``Console``."""
    return RichTheme(
        {
            "banner": f"bold {palette.banner}",
            "summary": f"bold {palette.summary}",
            "primary": palette.primary,
            "success": palette.success,
            "danger": palette.danger,
            "dim": palette.dim,
        }
    )


def to_prompt_style(palette: ColorPalette) -> PtStyle:
    """Convierte la paleta a un ``prompt_toolkit.Style``."""
    return PtStyle.from_dict(
        {
            "banner": f"bold {palette.banner}",
            "summary": f"bold {palette.summary}",
            "selected": f"reverse bold {palette.primary}",
            "checked": f"bold {palette.success}",
            "dim": palette.dim,
            "text": palette.text,
            "danger": palette.danger,
            "help": f"bg:{palette.help_bg} {palette.help_fg}",
            "tree": palette.primary,
        }
    )