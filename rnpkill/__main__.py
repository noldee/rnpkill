"""Permite ejecutar el paquete con `python -m rnpkill`."""
from __future__ import annotations

import sys

from rnpkill.cli.main import main

if __name__ == "__main__":
    sys.exit(main())