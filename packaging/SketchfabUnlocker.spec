# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec used by .github/workflows/build.yml
import os
import sys

from PyInstaller.utils.hooks import collect_submodules

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
IS_WINDOWS = sys.platform.startswith("win")

a = Analysis(
    [os.path.join(ROOT, "gui.py")],
    pathex=[ROOT],
    binaries=[],
    datas=[(os.path.join(ROOT, "ui"), "ui")],
    hiddenimports=["osgjs_convert", "fix_materials", "textures"] + collect_submodules("webview"),
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# On Linux never ship the C++ runtime or the graphics stack: they have to match the
# host's Mesa/driver libraries. A bundled (older) libstdc++ shadows the system one and
# makes EGL/Qt abort with "GLIBCXX_x.y.z not found" on newer distros.
if sys.platform.startswith("linux"):
    SYSTEM_LIBS = (
        "libstdc++.so", "libgcc_s.so",
        "libEGL.so", "libGL.so", "libGLX.so", "libGLdispatch.so", "libOpenGL.so",
        "libgbm.so", "libdrm", "libwayland-", "libva",
    )
    a.binaries = [b for b in a.binaries if not os.path.basename(b[0]).startswith(SYSTEM_LIBS)]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SketchfabUnlocker",
    debug=False,
    strip=False,
    upx=False,
    console=not IS_WINDOWS,  # windowed on Windows, keep the console (logs) on Linux
)
