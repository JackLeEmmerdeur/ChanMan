# -----------------------------------
# Todo:
# - Work with QT locales
# - Implement link-system in help
# - Complete help texts
# - Design app logo
# - About Qt-Disclaimer
# - Don't show path of opened file in mainwindow-title (may go to statusbar)
# - Localize buttons in question-messagebox
# - Tune performance of deletion in channel-treeview
# - Bug in line 485 (parent.internalPointer().removeChildByIndex(row))
#   in ChannelModel.deleteSelectedItems() when selection has gaps
# - CLEAN THE FROCK UP!
# -----------------------------------

# Don't refactor the following imports, as they are needed
# for pyinstaller to include them into the package.
# Otherwise the tv-plugins would try to load them,
# but they weren't included as PyInstaller did not
# recognize them, because the tvplugins dir was
# excluded in pyinstaller-spec-file
import ijson
import ijson.backends.yajl2 as ijson
import sortedcontainers
import plumbum

import PyQt5
import os
from lib.App import App
from sys import argv as sysargv
from pathlib import Path
from os import environ
import sys

from win_unicode_console import enable as win_uc_enable

dirname = os.path.dirname(PyQt5.__file__)

p1 = Path(dirname)
plugins = p1.joinpath("Qt", "plugins")
platformplugins = plugins.joinpath("platforms")
environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platformplugins.absolute())
environ["QT_PLUGIN_PATH"] = str(plugins.absolute())


def trap_exc_during_debug(*args):
	# when app raises uncaught exception, print info
	print(args)


# install exception hook: without this, uncaught exception would cause application to exit
sys.excepthook = trap_exc_during_debug

if __name__ == '__main__':
	win_uc_enable()
	app = App(sysargv, __file__)
	app.exec()
