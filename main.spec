# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


legacy_budget_template = None
for suffix in ('.xlsm', '.xlsx'):
    candidate = Path(f'CUSTO_PLASMA-LASER_V22_Definitiva-antigaa{suffix}')
    if candidate.exists():
        legacy_budget_template = (str(candidate), '.')
        break

datas = [
    ('planilha_orcamento_laser_plasma_ref_Rev1.xlsm', '.'),
    ('planilha-dbx.xlsx', '.'),
    ('codigo_database.xlsx', '.'),
    ('desktop_app/dbx-ly.ico', 'desktop_app'),
    ('desktop_app/dbx-ly.png', 'desktop_app'),
    ('desktop_app/dbx-ly.svg', 'desktop_app'),
    ('desktop_app/lyps-v22-tm2-svg.png', 'desktop_app'),
]
if legacy_budget_template is not None:
    datas.append(legacy_budget_template)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['desktop_app/dbx-ly.ico'],
)
