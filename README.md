<div align="center">

# 🧹 rnpkill

**A modern alternative to [`npkill`](https://github.com/voidcosmos/npkill), written in Python.**

Find and delete `node_modules`, virtual environments, and other heavy
development folders — with a collapsible tree UI, themes, age filters,
and historical reports.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)]()

**English** | [Español](README.es.md)

</div>

---

## ✨ Why another `node_modules` cleaner?

`npkill` is great, but it's built on Node.js, only targets `node_modules`
out of the box, and lacks themes, age filters, and report exports.
**`rnpkill` does.** It's pure Python, cross-platform, and with a UI
designed to be actually pleasant to use.

| Feature                                    | npkill | **rnpkill** |
| ------------------------------------------ | :----: | :---------: |
| **Node.js** — `node_modules`               |   ✅   |     ✅      |
| **Node.js** — `.next`, `.nuxt`, `.turbo`…  |   ❌   |     ✅      |
| **Python** — `venv`, `.venv`, `env`        |   ❌   |     ✅      |
| **Python** — `__pycache__`, `.tox`, caches |   ❌   |     ✅      |
| **Rust** — `target`                        |   ❌   |     ✅      |
| **Java / Kotlin** — `.gradle`, `.m2`       |   ❌   |     ✅      |
| **Go / PHP / Laravel** — `vendor`          |   ❌   |     ✅      |
| **Generic** — `dist`, `build`              |   ❌   |     ✅      |
| Collapsible tree UI                        |   ❌   |     ✅      |
| Themes (One Dark, Catppuccin…)             |   ❌   |     ✅      |
| `--older-than 90d` filter                  |   ❌   |     ✅      |
| `--dry-run`                                |   ✅   |     ✅      |
| **`--no-size` (instant scan)**             |   ❌   |     ✅      |
| JSON / CSV reports                         |   ❌   |     ✅      |
| History + statistics                       |   ❌   |     ✅      |
| Progress bar while deleting                |   ✅   |     ✅      |
| Incremental search `/`                     |   ❌   |     ✅      |

### What it detects out of the box

| Ecosystem              | Folders                                                          |
| ---------------------- | ---------------------------------------------------------------- |
| **Node.js / JS / TS**  | `node_modules`, `.next`, `.nuxt`, `.parcel-cache`, `.turbo`, `.svelte-kit` |
| **Python**             | `venv`, `.venv`, `env`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.tox` |
| **Rust**               | `target`                                                         |
| **Java / Kotlin**      | `.gradle`, `.m2`                                                 |
| **Go / PHP / Laravel** | `vendor`                                                         |
| **Generic bundlers**   | `dist`, `build`                                                  |

You can extend this list by editing `DEFAULT_TARGETS` in
[`rnpkill/core/scanner.py`](rnpkill/core/scanner.py).

---

## 🎬 Demo

```
██████╗ ███╗   ██╗██████╗ ██╗  ██╗██╗██╗     ██╗
██╔══██╗████╗  ██║██╔══██╗██║ ██╔╝██║██║     ██║
██████╔╝██╔██╗ ██║██████╔╝█████╔╝ ██║██║     ██║
██╔══██╗██║╚██╗██║██╔═══╝ ██╔═██╗ ██║██║     ██║
██║  ██║██║ ╚████║██║     ██║  ██╗██║███████╗███████╗
╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝

 Total space: 3.98 GB · 27 folder(s)

 ▼ ~/projects
   ❯ [X]  420.36 MB   3d    node_modules
     [ ]  261.94 MB   1mo   .venv
 ▼ ~/old-projects
     [ ]  238.74 MB   8mo   node_modules
     [ ]  181.69 MB   1y    node_modules
 ↑/↓ move · ←/→ collapse · space select · s/n/d sort · / search · enter confirm
```

---

## 🚀 Installation

### Option 1: Download a prebuilt binary (no Python required)

Grab the binary for your OS from the [latest release](https://github.com/noldee/rnpkill/releases/latest):

**macOS & Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/noldee/rnpkill/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://raw.githubusercontent.com/noldee/rnpkill/main/install.ps1 | iex"
```

Then run it from anywhere:

```bash
rnpkill
```

> On macOS you may need to right-click → Open the first time (Gatekeeper), since the binary isn't code-signed.

### Option 2: From source (requires Python 3.10+)

```bash
git clone https://github.com/noldee/rnpkill.git
cd rnpkill
python3 -m venv .venv
source .venv/bin/activate      # Linux / macOS
# .\.venv\Scripts\Activate.ps1 # Windows PowerShell
pip install -r requirements.txt
```

Install as a global command:

```bash
pip install -e .
rnpkill ~/Projects
```

Or with `pipx` (isolates the environment):

```bash
pipx install git+https://github.com/noldee/rnpkill.git
```

---

## 🎮 Usage

### Basic cases

```bash
# Scan the current directory
rnpkill

# Scan a specific path
rnpkill ~/Projects

# Limit recursion depth (useful on large disks)
rnpkill ~/Projects --max-depth 4

# Instant listing without computing sizes
# Useful on slow disks (external HDD, NTFS via ntfs-3g, network drives)
rnpkill ~/Projects --no-size
```

> **Performance tip**: On network drives, external HDDs, or NTFS partitions
> mounted on Linux, computing sizes can be slow because the OS must read
> metadata for every file. Use `--no-size` to list folders instantly and
> skip the size measurement step.

### Filters and preview

```bash
# Only folders untouched for 90 days
rnpkill ~/Projects --older-than 90d

# Simulation: shows what would be deleted, without touching anything
rnpkill ~/Projects --dry-run

# Export a session report
rnpkill ~/Projects --report ~/report.json
rnpkill ~/Projects --report ~/report.csv
```

### Themes

```bash
rnpkill ~/Projects --theme catppuccin
rnpkill ~/Projects --theme one-dark
rnpkill ~/Projects --theme dracula
rnpkill ~/Projects --theme gruvbox
rnpkill ~/Projects --theme nord
rnpkill ~/Projects --theme solarized
```

### History and statistics

```bash
rnpkill --history              # last 10 cleanups
rnpkill --stats                # total freed historically
rnpkill --export-history h.csv # export everything to CSV
```

### Full CLI reference

| Flag                | Description                                          |
| ------------------- | ---------------------------------------------------- |
| `path`              | Root directory to scan (default: current dir)        |
| `--max-depth N`     | Limit recursion depth                                |
| `--no-size`         | Skip size measurement (instant listing)              |
| `--older-than X`    | Only folders untouched for X (e.g. `90d`, `6m`, `1y`) |
| `--dry-run`         | Show what would be deleted, without deleting         |
| `--report FILE`     | Export a JSON or CSV report of the session           |
| `--theme NAME`      | UI theme (default, one-dark, catppuccin…)            |
| `--history`         | Show the last 10 cleanups and exit                   |
| `--stats`           | Show aggregate statistics and exit                   |
| `--export-history F`| Export the full history to a CSV file and exit       |

---

## ⌨️ Controls

| Key               | Action                              |
| ----------------- | ----------------------------------- |
| `↑` `↓` / `k` `j` | Navigate                            |
| `←` `→` / `h` `l` | Collapse / expand project           |
| `space`           | Toggle selection (project = all)    |
| `a`               | Toggle everything                   |
| `s` / `n` / `d`   | Sort by size / name / date          |
| `p`               | Sort by path                        |
| `/`               | Incremental search                  |
| `enter`           | Confirm selection                   |
| `q` / `Esc`       | Cancel and exit                     |
| `Ctrl+C`          | Interrupt                           |

---

## 🏗️ Architecture

Designed following **SOLID**, **Clean Code**, and strict layer
separation:

```
rnpkill/
├── main.py                      # Composition root (thin entry point)
└── rnpkill/
    ├── __main__.py              # Enables `python -m rnpkill`
    ├── cli/                     # Command-line layer
    │   ├── args.py              # argparse definitions
    │   ├── commands.py          # --history, --stats, --export-history
    │   └── app.py               # RnpkillApp orchestrator
    ├── core/                    # Pure domain (no UI, no CLI)
    │   ├── models.py            # TargetFolder, Project
    │   ├── scanner.py           # Filesystem walker
    │   ├── size_calculator.py   # Fast size measurement (du / parallel)
    │   ├── deleter.py           # Safe deletion with error handling
    │   ├── age_filter.py        # --older-than parsing & filtering
    │   ├── history.py           # Persistent history (JSONL)
    │   └── reporter.py          # JSON / CSV reports
    ├── ui/                      # Presentation (prompt_toolkit + rich)
    │   ├── banner.py            # ASCII banner + palette
    │   ├── menu.py              # Menu orchestrator
    │   ├── navigation.py        # Cursor, grouping, selection state
    │   ├── renderer.py          # Text formatting (rows, summary, help)
    │   ├── layout_builder.py    # prompt_toolkit layout assembly
    │   ├── keybindings.py       # Keyboard shortcuts
    │   └── progress.py          # Deletion progress bar
    └── utils/                   # Cross-cutting helpers
        ├── formatters.py        # bytes → MB/GB
        ├── paths.py             # Cross-platform path & XDG helpers
        ├── terminal.py          # Terminal clear / detection
        └── themes.py            # Color themes (One Dark, Catppuccin…)
```

### Layer rules

- **`cli/`** — Parses arguments and orchestrates. Depends on `core` and `ui`.
- **`core/`** — Pure domain logic. **Does not depend** on `ui`, `cli`, or presentation `utils`.
- **`ui/`** — Presentation layer. Depends on `core` (models only), never the other way around.
- **`utils/`** — Cross-cutting helpers. No business logic.

Each module has **a single responsibility** and is testable in isolation.

---

## ⚡ Performance

- On Linux/macOS it uses `du -sb` (native C) → **50-100× faster** than
  walking the tree in pure Python.
- On Windows it falls back to a parallel walk with `ThreadPoolExecutor`.
- With `--no-size`, listing is **instantaneous** even on disks with
  hundreds of thousands of files.

Benchmark on 27 `node_modules` folders (≈4 GB) on a **SATA SSD**:

| Method               | Time     |
| -------------------- | -------- |
| Pure Python          | ~180 s   |
| Parallel walk        | ~25 s    |
| **`du -sb` + pool**  | **~2 s** |

> ⚠️ **Note about slow filesystems**: On external HDDs, network drives, or
> NTFS partitions mounted via `ntfs-3g` on Linux, size measurement can be
> 100× slower because the OS reads metadata for every file. In those cases,
> use `--no-size` for an instant listing.

---

## 🗺️ Roadmap

- [x] Fast scanning with `du`
- [x] Collapsible tree and themes
- [x] `--older-than`, `--dry-run` filters
- [x] `--no-size` for slow filesystems
- [x] JSON/CSV reports, history and statistics
- [x] Standalone binaries via PyInstaller
- [ ] Tests with `pytest`
- [ ] PyPI release
- [ ] Per-language plugins

---

## 🤝 Contributing

PRs are welcome. Before submitting:

1. Fork the repo.
2. Create a branch: `git checkout -b feat/my-feature`.
3. Follow the existing architecture (respect SOLID/SRP).
4. Add type hints and docstrings.
5. Open the PR with a clear description.

For bugs, open an issue with:

- OS and Python version.
- Exact command run.
- Full output (including the traceback).

---

## 📄 License

MIT © 2025 Walter — see [LICENSE](LICENSE).

---

<div align="center">

**Saved you some GB? Give the repo a ⭐.**

</div>
