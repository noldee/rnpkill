# rnpkill.spec
# Configuración de PyInstaller para rnpkill.
# Genera un ejecutable único por plataforma sin dependencias externas.
# Build:  pyinstaller --clean rnpkill.spec

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # prompt_toolkit y rich cargan módulos dinámicamente
        'prompt_toolkit',
        'prompt_toolkit.layout',
        'prompt_toolkit.key_binding',
        'prompt_toolkit.styles',
        'rich',
        'rich.console',
        'rich.progress',
        'rich.table',
        'rich.panel',
        'questionary',
        'rnpkill',
        'rnpkill.core',
        'rnpkill.ui',
        'rnpkill.utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='rnpkill',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,          # comprime el binario (necesita UPX instalado)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,      # CLI → true
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)