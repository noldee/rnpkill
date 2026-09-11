"""Definición y parseo de los argumentos de línea de comandos."""
from __future__ import annotations

import argparse

from rnpkill.utils.themes import list_theme_names


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser de argparse con todos los flags."""
    parser = argparse.ArgumentParser(
        prog="rnpkill",
        description="Busca y elimina carpetas pesadas de desarrollo.",
    )
    parser.add_argument(
        "path", nargs="?", default=".", help="Raíz a escanear."
    )
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument(
        "--no-size",
        action="store_true",
        help="No calcular tamaños (listado instantáneo).",
    )
    parser.add_argument(
        "--older-than",
        default=None,
        help="Solo carpetas sin tocar en X (ej: 90d, 6m, 1y).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostrar qué se borraría sin tocar nada.",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Ruta de salida para reporte (.json o .csv).",
    )
    parser.add_argument(
        "--theme",
        default="default",
        choices=list_theme_names(),
        help="Tema de color de la UI.",
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="Mostrar las últimas 10 limpiezas y salir.",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Mostrar estadísticas agregadas y salir.",
    )
    parser.add_argument(
        "--export-history",
        default=None,
        help="Exportar historial completo a CSV y salir.",
    )
    return parser


def parse_args() -> argparse.Namespace:
    """Parsea ``sys.argv`` y devuelve el namespace."""
    return build_parser().parse_args()