# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for CCSS - Claude Code Session Search.

This spec file is committed to the repository and used by scripts/build.py.
Do not delete - it contains all hidden imports needed for the standalone binary.
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Entry point
entry_script = 'src/ccss/cli.py'

# Collect all submodules for complex packages
textual_datas, textual_binaries, textual_hiddenimports = collect_all('textual')
rich_datas, rich_binaries, rich_hiddenimports = collect_all('rich')

# Hidden imports - packages PyInstaller misses
hiddenimports = [
    # === Textual framework (TUI) ===
    'textual',
    'textual.app',
    'textual.binding',
    'textual.containers',
    'textual.screen',
    'textual.timer',
    'textual.widgets',
    'textual.widgets.input',
    'textual.widgets.option_list',
    'textual.theme',
    'textual._context',
    'textual._xterm_parser',
    'textual.css',
    'textual.css.query',
    'textual.css.parse',
    'textual.css.stylesheet',
    'textual.dom',
    'textual.driver',
    'textual.drivers',
    'textual.drivers.linux_driver',
    'textual.geometry',
    'textual.message',
    'textual.reactive',
    'textual.renderables',
    'textual.strip',
    'textual.scroll_view',
    'textual.widget',
    'textual.events',
    'textual.keys',
    'textual.command',
    'textual.content',
    'textual.visual',

    # === Rich (console formatting) ===
    'rich',
    'rich.text',
    'rich.console',
    'rich.markup',
    'rich.style',
    'rich.segment',
    'rich.syntax',
    'rich.highlighter',
    'rich.panel',
    'rich.table',
    'rich.box',
    'rich.color',
    'rich.terminal_theme',
    'rich.traceback',

    # === Typer/Click CLI ===
    'typer',
    'typer.main',
    'typer.core',
    'typer.rich_utils',
    'click',
    'click.core',
    'click.decorators',
    'click.exceptions',
    'click.formatting',
    'click.parser',
    'click.termui',
    'click.types',
    'click.utils',

    # === Other dependencies ===
    'pyperclip',
    'pygments',
    'pygments.lexers',
    'pygments.styles',
    'pygments.formatters',
    'markdown_it',
    'markdown_it.main',
    'linkify_it',
    'mdit_py_plugins',
    'uc_micro',
    'mdurl',

    # === Standard library (sometimes missed) ===
    'sqlite3',
    'json',
    'logging',
    'logging.handlers',
    'subprocess',
    'atexit',
    'signal',
    'threading',
    'zipfile',
    'dataclasses',
    'typing',
    'pathlib',
    're',
    'collections',
    'collections.abc',
    'datetime',
    'os',
    'sys',
    'time',
]

# Merge collected imports
hiddenimports.extend(textual_hiddenimports)
hiddenimports.extend(rich_hiddenimports)
hiddenimports = list(set(hiddenimports))  # Remove duplicates

# Data files (CSS, themes, etc.)
datas = []
datas.extend(textual_datas)
datas.extend(rich_datas)

# Binaries
binaries = []
binaries.extend(textual_binaries)
binaries.extend(rich_binaries)

# Analysis
a = Analysis(
    [entry_script],
    pathex=['src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude dev/test packages
        'pytest',
        'pytest_asyncio',
        'pytest_rerunfailures',
        'pyright',
        'ruff',
        # Exclude unused optional features
        'tkinter',
        'matplotlib',
        'numpy',
        'PIL',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ccss',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
