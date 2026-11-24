# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)

datas = []
binaries = []
hiddenimports = ["captcha_assist"]

# Bundle Selenium Manager binary, metadata, and lazy-loaded webdriver submodules
datas += collect_data_files("selenium")
binaries += collect_dynamic_libs("selenium")
hiddenimports += collect_submodules("selenium")

# Bundle ddddocr ONNX models, submodules, & onnxruntime native C-API binaries
datas += collect_data_files("ddddocr")
hiddenimports += collect_submodules("ddddocr")
binaries += collect_dynamic_libs("onnxruntime")
hiddenimports += collect_submodules(
    "onnxruntime",
    filter=lambda name: not name.startswith(
        ("onnxruntime.quantization", "onnxruntime.transformers", "onnxruntime.tools")
    ),
)

a_settings = Analysis(
    ["settings.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

a_bot = Analysis(
    ["chrome_tixcraft.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

MERGE(
    (a_settings, "settings", "settings"),
    (a_bot, "chrome_tixcraft", "chrome_tixcraft"),
)

pyz_settings = PYZ(a_settings.pure)
exe_settings = EXE(
    pyz_settings,
    a_settings.scripts,
    [],
    exclude_binaries=True,
    name="settings",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

pyz_bot = PYZ(a_bot.pure)
exe_bot = EXE(
    pyz_bot,
    a_bot.scripts,
    [],
    exclude_binaries=True,
    name="chrome_tixcraft",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe_settings,
    a_settings.binaries,
    a_settings.datas,
    exe_bot,
    a_bot.binaries,
    a_bot.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="tixcraft_bot",
)
