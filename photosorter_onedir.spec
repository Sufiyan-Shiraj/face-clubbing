# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os
import sys

block_cipher = None

datas = [
    ('frontend/dist', 'frontend/dist'),
]

datas += collect_data_files('insightface')

import insightface
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

hiddenimports += collect_submodules('uvicorn')
hiddenimports += collect_submodules('insightface')
hiddenimports += collect_submodules('webview')

if os.path.exists('VERSION'):
    datas.append(('VERSION', '.'))

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        '_tkinter',
        'matplotlib',
        'pytest',
        'IPython',
        'docutils',
        'pygments',
        'tests',
        'eval',
        'scratch',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

is_windows = sys.platform.startswith('win')
icon_file = 'catlog.ico' if os.path.exists('catlog.ico') else None
version_file = 'version_info.txt' if is_windows and os.path.exists('version_info.txt') else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CatLog',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
    version=version_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CatLog_onedir',
)
