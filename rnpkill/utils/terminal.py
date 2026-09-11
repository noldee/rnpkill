import sys


def clear_terminal() -> None:
    """Limpia pantalla y scrollback de forma multiplataforma.

    Usa códigos ANSI explícitos en lugar de ``rich.Console.clear()``
    porque este último no siempre surte efecto cuando se invoca en
    medio de la ejecución de la aplicación.
    """
    # \033[2J  → borra pantalla
    # \033[3J  → borra scrollback
    # \033[H   → cursor a home (0,0)
    sys.stdout.write("\033[2J\033[3J\033[H")
    sys.stdout.flush()