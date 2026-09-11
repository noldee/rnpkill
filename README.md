<div align="center">

# 🧹 rnpkill

**Alternativa moderna a [`npkill`](https://github.com/voidcosmos/npkill), escrita en Python puro.**

Encuentra y elimina `node_modules`, entornos virtuales y otras carpetas
pesadas de desarrollo — con árbol plegable, temas, filtros por antigüedad
y reportes históricos.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)]()

</div>

---

## ✨ ¿Por qué otro limpiador de `node_modules`?

`npkill` es genial, pero está en Node.js y no cubre bien entornos
Python, ni ofrece temas, ni permite filtrar por antigüedad o exportar
reportes. **`rnpkill` sí.** Es Python puro, multiplataforma y con una
UI pensada para ser cómoda de verdad.

| Feature                         | npkill | **rnpkill** |
| ------------------------------- | :----: | :---------: |
| Detecta `node_modules`          |   ✅   |     ✅      |
| Detecta `venv`, `.venv`, `env`  |   ❌   |     ✅      |
| Detecta `__pycache__`, `.next`… |   ❌   |     ✅      |
| Árbol plegable                  |   ❌   |     ✅      |
| Temas (One Dark, Catppuccin…)   |   ❌   |     ✅      |
| Filtro `--older-than 90d`       |   ❌   |     ✅      |
| `--dry-run`                     |   ❌   |     ✅      |
| Reportes JSON / CSV             |   ❌   |     ✅      |
| Historial + estadísticas        |   ❌   |     ✅      |
| Barra de progreso al borrar     |   ✅   |     ✅      |
| Búsqueda incremental `/`        |   ❌   |     ✅      |

---

## 🎬 Demo

```
██████╗ ███╗   ██╗██████╗ ██╗  ██╗██╗██╗     ██╗
██╔══██╗████╗  ██║██╔══██╗██║ ██╔╝██║██║     ██║
██████╔╝██╔██╗ ██║██████╔╝█████╔╝ ██║██║     ██║
██╔══██╗██║╚██╗██║██╔═══╝ ██╔═██╗ ██║██║     ██║
██║  ██║██║ ╚████║██║     ██║  ██╗██║███████╗███████╗
╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝

 Espacio total: 3.98 GB · 27 carpeta(s)

 ▼ ~/projects
   ❯ [X]  420.36 MB   3d   node_modules
     [ ]  261.94 MB   1mo  .venv
 ▼ ~/old-projects
     [ ]  238.74 MB   8mo  node_modules
     [ ]  181.69 MB   1y   node_modules
 ↑/↓ mover · ←/→ plegar · espacio marcar · s/n/d ordenar · / buscar · enter confirmar
```

---

## 🚀 Instalación

### Requisitos

- Python **3.10+**
- `du` (viene por defecto en Linux/macOS; en Windows se usa fallback puro Python)

### Desde el código fuente

```bash
git clone https://github.com/<tu-usuario>/rnpkill.git
cd rnpkill
python3 -m venv .venv
source .venv/bin/activate      # Linux / macOS
# .\.venv\Scripts\Activate.ps1 # Windows PowerShell
pip install -r requirements.txt
```

### Instalación como comando global (recomendado)

```bash
pip install -e .
rnpkill ~/Projects
```

O con `pipx` (aísla el entorno):

```bash
pipx install git+https://github.com/<tu-usuario>/rnpkill.git
```

---

## 🎮 Uso

### Casos básicos

```bash
# Escanear el directorio actual
rnpkill

# Escanear una ruta concreta
rnpkill ~/Projects

# Limitar profundidad (útil en discos grandes)
rnpkill ~/Projects --max-depth 4

# Listado instantáneo sin calcular tamaños
rnpkill ~/Projects --no-size
```

### Filtros y preview

```bash
# Solo lo que no se toca en 90 días
rnpkill ~/Projects --older-than 90d

# Simulación: muestra qué borraría, sin tocar nada
rnpkill ~/Projects --dry-run

# Exportar reporte de la sesión
rnpkill ~/Projects --report ~/reporte.json
rnpkill ~/Projects --report ~/reporte.csv
```

### Temas

```bash
rnpkill ~/Projects --theme catppuccin
rnpkill ~/Projects --theme one-dark
rnpkill ~/Projects --theme dracula
rnpkill ~/Projects --theme gruvbox
rnpkill ~/Projects --theme nord
rnpkill ~/Projects --theme solarized
```

### Historial y estadísticas

```bash
rnpkill --history              # últimas 10 limpiezas
rnpkill --stats                # total liberado histórico
rnpkill --export-history h.csv # exportar todo a CSV
```

---

## ⌨️ Controles

| Tecla             | Acción                                |
| ----------------- | ------------------------------------- |
| `↑` `↓` / `k` `j` | Navegar                               |
| `←` `→` / `h` `l` | Plegar / desplegar proyecto           |
| `espacio`         | Marcar / desmarcar (proyecto = todos) |
| `a`               | Marcar / desmarcar todo               |
| `s` / `n` / `d`   | Ordenar por tamaño / nombre / fecha   |
| `p`               | Ordenar por ruta                      |
| `/`               | Búsqueda incremental                  |
| `enter`           | Confirmar selección                   |
| `q` / `Esc`       | Cancelar y salir                      |
| `Ctrl+C`          | Interrumpir                           |

---

## 🏗️ Arquitectura

Diseñado siguiendo **SOLID**, **Clean Code** y separación estricta de capas:

```
rnpkill/
├── main.py                  # Composition root
└── rnpkill/
    ├── core/                # Dominio puro (sin UI, sin CLI)
    │   ├── models.py
    │   ├── scanner.py
    │   ├── size_calculator.py
    │   ├── deleter.py
    │   ├── age_filter.py
    │   ├── history.py
    │   └── reporter.py
    ├── ui/                  # Presentación (prompt_toolkit + rich)
    │   ├── banner.py
    │   ├── menu.py
    │   └── progress.py
    └── utils/               # Helpers transversales
        ├── formatters.py
        ├── paths.py
        └── themes.py
```

- **`core`** no depende de `ui` ni de `utils` de presentación.
- **`ui`** depende de `core` (modelos) pero no al revés.
- Cada módulo tiene **una sola responsabilidad** y es testeable aislado.

---

## ⚡ Rendimiento

- En Linux/macOS usa `du -sb` (C nativo) → **50-100× más rápido** que
  recorrer el árbol con Python puro.
- En Windows cae a un walk paralelo con `ThreadPoolExecutor`.
- Con `--no-size`, el listado es **instantáneo** incluso en discos con
  cientos de miles de archivos.

Benchmark orientativo sobre 27 `node_modules` (≈4 GB):

| Método              | Tiempo   |
| ------------------- | -------- |
| Python puro         | ~180 s   |
| Walk paralelo       | ~25 s    |
| **`du -sb` + pool** | **~2 s** |

---

## 🗺️ Roadmap

- [x] Escaneo rápido con `du`
- [x] Árbol plegable y temas
- [x] Filtros `--older-than`, `--dry-run`
- [x] Reportes JSON/CSV, historial y estadísticas
- [ ] Tests con `pytest`
- [ ] Publicación en PyPI
- [ ] Plugins por lenguaje
- [ ] Binarios standalone con PyInstaller

---

## 🤝 Contribuir

Las PRs son bienvenidas. Antes de enviar:

1. Haz fork del repo.
2. Crea una rama: `git checkout -b feat/mi-feature`.
3. Sigue la arquitectura existente (respeta SOLID/SRP).
4. Añade type hints y docstrings.
5. Abre la PR con descripción clara.

Para bugs, abre un issue con:

- SO y versión de Python.
- Comando exacto ejecutado.
- Salida completa (incluyendo el traceback).

---

## 📄 Licencia

MIT © 2025 Walter — ver [LICENSE](LICENSE).

---

<div align="center">

**¿Te ahorró GB? Dale una ⭐ al repo.**

</div>
