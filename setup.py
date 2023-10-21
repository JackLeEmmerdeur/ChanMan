import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
buildoptions = dict(
    include_files=["tvplugins/", "gui/", "lib/", "model/", "icons_rc.py", "icons_search_rc.py"],
    packages=["six", "ijson", "sortedcontainers", "plumbum", "chardet", "json", "pathlib", "typing", "PyQt5"],
    namespace_packages=["ruamel.yaml"]
)

executables = [
    Executable('main.py', base=None, targetName='test')
]


# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(name="test",
      version="0.1",
      description="My GUI application!",
      options=dict(build_exe=buildoptions),
      executables=executables)