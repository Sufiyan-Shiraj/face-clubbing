# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

datas = [
    ('frontend/dist', 'frontend/dist'),
]

# Collect any package data files for insightface and onnxruntime
datas += collect_data_files('insightface')

import insightface
import os
insightface_dir = os.path.dirname(insightface.__file__)
objects_dir = os.path.join(insightface_dir, 'data', 'objects')
if os.path.exists(objects_dir):
    datas.append((objects_dir, 'objects'))

hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'webview',
    'webview.platforms.winforms',
    'webview.platforms.edgechromium',
    'fastapi',
    'fastapi.staticfiles',
    'starlette',
    'starlette.staticfiles',
    'insightface',
    'insightface.app',
    'insightface.model_zoo',
    'onnxruntime',
    'sklearn',
    'sklearn.utils._typedefs',
    'sklearn.neighbors._typedefs',
    'scipy',
    'scipy.spatial.distance',
    'cv2',
    'PIL',
    'pillow_heif',
]

# Add submodules
hiddenimports += collect_submodules('uvicorn')
hiddenimports += collect_submodules('insightface')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='photosorter',
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
)
