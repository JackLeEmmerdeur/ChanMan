# -----------------------------------
# Python libs
# Use Path.home() in Python 3.5+
# -----------------------------------
from os.path import join as pjoin
from pathlib import Path
from typing import Any
import sys
from sys import argv as sysargv, exit as sysexit

# -----------------------------------
# Qt
# -----------------------------------
from PyQt5.Qt import Qt, QObject, pyqtSlot
from PyQt5.QtCore import QItemSelection, QModelIndex, QEvent, QPoint
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QApplication, QFileDialog, QListWidgetItem

# -----------------------------------
# YAML
# -----------------------------------
from ruamel.yaml import YAML

# -----------------------------------
# GUI
# -----------------------------------
from gui.MainWindow import Ui_MainWindow
from gui.MainWindowWrapper import MainWindowWrapper
from gui.SearchDialogWrapper import SearchDialogWrapper
from gui.HelpDialogWrapper import HelpDialogWrapper

# -----------------------------------
# Helpers
# -----------------------------------
from lib.Helpers import string_is_empty, load_modules, nested_set, nested_get, get_user_folder, UserFolderType, \
	get_reformatted_exception, is_empty_sequence, file_exists, mkdir, get_executable_dirname, is_integerish, \
	get_roaming_apppath, copy_file
from lib.Logger import Logger
from lib.QTHelpers import messagebox, question, setStyle

# -----------------------------------
# Application
# -----------------------------------
from model.ChannelModel import ChannelModel


class App(QObject):
	run_from_ide = None
	""":type: bool"""

	bundle_dir = None
	""":type: str"""

	maindirpath = None
	""":type: str"""

	channeltype = None

	channeltypefilter = None
	""":type:str"""

	model = None
	""":type:ChannelModel"""

	prevmessagebox = None
	""":type: QMessageBox"""

	ui = None
	""":type: Ui_MainWindow"""

	mainwindow = None
	""":type: MainWindowWrapper"""

	searchdialog = None
	""":type: SearchDialogWrapper"""

	helpdialog = None
	""":type: HelpDialogWrapper"""

	pluginregistry = None
	""":type: PluginsRegistry"""

	# Last opened filename
	last_filename = None
	""":type:str"""

	# Last opened additional filenames
	last_additionalfiles = None
	""":type:list(str)"""

	# Last pluginmodule determined from fileselection
	pluginmodule = None
	""":type:dict"""

	app = None
	""":type:QApplication"""

	log = None
	""":type:Logger"""

	userapppath = None
	""":type: Path"""

	yaml = None
	""":type:YAML"""

	yaml_config = None

	yamlfilepath = None

	use_file_logger = None
	""":type: bool"""

	def __init__(self, argv, mainfile):
		super(App, self).__init__()
		try:
			self.run_from_ide = True

			if getattr(sys, 'frozen', False):
				# we are running in a bundle
				self.run_from_ide = False
				self.bundle_dir = sys._MEIPASS
				print("self.bundle_dir={}".format(self.bundle_dir))

			print("self.run_from_ide={}".format(self.run_from_ide))

			# -----------------------------------
			# Setup application
			# -----------------------------------
			self.app = QApplication(argv)
			self.app.aboutToQuit.connect(self.onAppAboutToQuit)
			self.maindirpath = get_executable_dirname(mainfile)
			self.userapppath = get_roaming_apppath("buccaneersdan", "ChanMan")
			print("self.maindirpath={}".format(self.maindirpath))
			print("self.userapppath={}".format(str(self.userapppath.absolute())))

			# -----------------------------------
			# Read program configuration
			# -----------------------------------
			configpath = self.userapppath.joinpath("config")
			print("configpath={}".format(str(configpath.absolute())))
			if not configpath.exists():
				mkdir(str(configpath.absolute()))

			configyamlpath = configpath.joinpath("config.yaml")
			configjsonpath = configpath.joinpath("log.json")

			if not configyamlpath.exists():
				if not self.run_from_ide:
					sourceyaml = Path(self.bundle_dir).joinpath("config", "config.yaml")
				else:
					sourceyaml = Path(self.maindirpath).joinpath("config", "config.yaml")
				copy_file(str(sourceyaml.absolute()), str(configyamlpath.absolute()))

			if not configjsonpath.exists():
				if not self.run_from_ide:
					sourcejson = Path(self.bundle_dir).joinpath("config", "log.json")
				else:
					sourcejson = Path(self.maindirpath).joinpath("config", "log.json")

				with open(str(sourcejson.absolute()), "rt") as jsonin:
					with open(str(configjsonpath.absolute()), "wt") as jsonout:
						errorlogfile = self.userapppath.joinpath("logs", "error.log")
						infologfile = self.userapppath.joinpath("logs", "info.log")

						for jsoninline in jsonin:
							if jsoninline.find('"filename":') > -1:
								jsonin_mod = '          "filename": "'
								if jsoninline.find("error.log") > -1:
									jsonin_mod += str(errorlogfile.absolute()).replace("\\", "/")
								else:
									jsonin_mod += str(infologfile.absolute()).replace("\\", "/")
								jsonout.write(jsonin_mod + "\",\n")
							else:
								jsonout.write(jsoninline)

			self.yamlOpen(str(configyamlpath.absolute()))

			# -----------------------------------
			# Prepare Logger
			# -----------------------------------
			use_file_logger = self.yamlGet("main", "use_file_logger")
			self.use_file_logger = False if use_file_logger is None else use_file_logger

			if self.use_file_logger:
				logpath = self.userapppath.joinpath("logs")

				if not logpath.exists():
					mkdir(str(logpath.absolute()))
				self.log = Logger(str(configjsonpath.absolute()))
				self.log.startlogger()
				self.log_info("=======================================")
				self.log_info("Programmstart")
				self.log_info("Lade TV-Plugins")

			# -----------------------------------
			# Load TV-Plugins and PluginRegistry
			# -----------------------------------
			modules = load_modules(
				pjoin(self.maindirpath, "tvplugins"),
				[
					["tvplugins.ITVPlugin.ITVPlugin", "ITVPlugin.py"],
					["tvplugins.PluginsRegistry.PluginsRegistry", "PluginsRegistry.py"]
				],
				["__", "assets", "__init__", "Images"],
				"TVPlugin"
			)

			plugins = []

			for module in modules:
				if hasattr(module, "PluginsRegistry"):
					self.pluginregistry = module.PluginsRegistry()

			for module in modules:
				if hasattr(module, "TVPlugin"):
					plugins.append(module.TVPlugin(self))

			self.pluginregistry.plugPlugins(plugins)
			self.pluginregistry.setPluginPath(self.maindirpath)
			self.channeltypefilter = self.pluginregistry.getFileFilters()

			# -----------------------------------
			# Setup Main-Window
			# -----------------------------------
			self.log_info("GUI einrichten")
			self.ui = Ui_MainWindow()
			self.mainwindow = MainWindowWrapper(self.ui)
			self.mainwindow.connectKeyPressEvent(self.onMainWindowKeyPress)
			self.ui.progressBar.hide()

			# -----------------------------------
			# Setup mainmenu-/toolbar-actions
			# -----------------------------------
			self.log_info("Toolbar einrichten")
			self.ui.actionOpen.triggered.connect(self.onOpenFile)
			self.ui.actionSave.triggered.connect(self.onSaveFile)
			self.ui.actionSaveAs.triggered.connect(self.onSaveFileAs)
			self.ui.actionDelete.triggered.connect(self.onDeleteItems)
			self.ui.actionSearch.triggered.connect(self.onShowSearchDialog)
			self.ui.actionHelp.triggered.connect(lambda: self.onShowHelpDialog("exportchannels"))
			self.ui.actionSearch.setEnabled(False)
			self.ui.actionDelete.setEnabled(False)
			self.ui.actionSave.setEnabled(False)
			self.ui.actionSaveAs.setEnabled(False)

			# -----------------------------------
			# Setup Help-Dialog
			# -----------------------------------
			self.log_info("Hilfe einrichten")
			self.helpdialog = HelpDialogWrapper(self.maindirpath, self.pluginregistry)

			# -----------------------------------
			# Setup Search-Dialog
			# -----------------------------------
			self.log_info("Suche einrichten")
			self.searchdialog = SearchDialogWrapper(self)

			# -----------------------------------
			# Setup channel treeview
			# -----------------------------------
			self.log_info("Hauptansicht einrichten")
			treeview = self.ui.treeView
			self.model = ChannelModel(self.ui, self.yamlGet("ui", "context_maxsortlevels"))
			treeview.installEventFilter(self.model)
			self.selmodel = treeview.selectionModel()
			self.selmodel.selectionChanged.connect(self.onTreeviewSelChanged)

			# -----------------------------------
			# Setup Statusbar
			# -----------------------------------
			self.ui.labelStatus1.setText("Gesamt:")
			self.ui.labelStatus2.setText("Kategorie:")

			setStyle(self.app, "Fusion")

			self.mainwindow.show()

		except Exception as e:
			messagebox(None, "Fehler", str(e), None, get_reformatted_exception("", e))
			sysexit()

	def exec(self):
		try:
			sysexit(self.app.exec_())
		except Exception as e:
			messagebox(self.prevmessagebox, "Fehler", "Application phased out", "", get_reformatted_exception("", e))

	def eventFilter(self, widget: QObject, event: QEvent):
		# if event.type() == QEvent.KeyPress:
		# 	if event.key() == Qt.Key_Print:
		# 		return True
		# return False
		return True

	def log_info(self, infotext, *args, **kwargs):
		if self.use_file_logger:
			self.log.info(infotext, *args, **kwargs)

	def resetModel(self):
		if self.model is not None:
			self.model.reset()

	def onShowSearchDialog(self):
		self.searchdialog.show()

	def onMainWindowKeyPress(self, e: QKeyEvent):
		pass

	def onAppAboutToQuit(self):
		if self.use_file_logger and self.log is not None:
			self.log.shutdown()
		print("CLEAN THE FROCK UP!")

	def onShowHelpDialog(self, helptype):
		self.helpdialog.showWindow()

	def onTreeviewSelChanged(self, selected: QItemSelection, deselected: QItemSelection):
		count = self.model.selectedCategoryCount()
		text = "Kategorie: {}".format("" if count is None else count)
		self.ui.labelStatus2.setText(text)

		# Check if a parent-item (TV, Radio, etc...) was selected and
		# grey out Delete-Action if so
		valid_deletion = True
		indicies = self.model.treeview.selectionModel().selectedIndexes()
		for index in indicies:  # type: QModelIndex
			if index.column() == 0:
				if index.parent().internalPointer() is None:
					valid_deletion = False
					break
		self.ui.actionDelete.setEnabled(valid_deletion)

	def yamlGet(self, *yamlkeychain):
		yamlval = nested_get(self.yaml_config, yamlkeychain)
		if not string_is_empty(yamlval, True):
			yamlval = yamlval.strip()
		return yamlval

	def yamlOpen(self, yamlfilepath: str):
		self.yamlfilepath = yamlfilepath
		with open(yamlfilepath, "rt") as yamlfile:
			self.yaml = YAML()
			self.yaml_config = self.yaml.load(yamlfile)

	def yamlSet(self, value, *yamlkeychain):
		nested_set(self.yaml_config, value, False, yamlkeychain)
		with open(self.yamlfilepath, "wt") as configfile:
			self.yaml.dump(self.yaml_config, configfile)

	def onSaveFileAs(self):
		last_saveas_folderpath = self.yamlGet("main", "last_saveas_folderpath")
		if string_is_empty(last_saveas_folderpath):
			last_saveas_folderpath = get_user_folder(UserFolderType.Desktop)
		last_saveas_folderpath = self.model.saveAs(
			self.mainwindow,
			self.pluginmodule,
			str(last_saveas_folderpath),
			self.last_additionalfiles
		)
		if not string_is_empty(last_saveas_folderpath):
			self.yamlSet(last_saveas_folderpath, "main", "last_saveas_folderpath")

	def onSaveFile(self):
		if not string_is_empty(self.last_filename):
			if question(
				self.mainwindow,
				"", "Wollen Sie die Original-Datei wirklich ueberschreiben?",
				False
			):
				self.model.save(self.pluginmodule, self.last_filename, self.last_additionalfiles)

	def onOpenFile(self):

		defaultfilepath = self.yamlGet("main", "lastchannel_filepath")

		if string_is_empty(defaultfilepath):
			defaultfilepath = str(get_user_folder(UserFolderType.Desktop))

		filepath, filefilter = QFileDialog.getOpenFileName(
			self.mainwindow,
			"Kanalliste öffnen",
			defaultfilepath,
			self.channeltypefilter)

		# Write opened file directory to YAML-Configfile
		if string_is_empty(filepath) or string_is_empty(filefilter):
			return

		lastchannel_filepath = str(Path(filepath).parent)
		last_filename = filepath
		pluginmodule = self.pluginregistry.getPluginByFileFilter(filefilter)
		last_additionalfiles = None

		if not is_empty_sequence(pluginmodule["additionalfilefilter"]):
			additionalfilefilters = pluginmodule["additionalfilefilter"]

			invalid_additional = False

			for additionalfilefilter in additionalfilefilters:
				additional_filepath, additional_filefilter = QFileDialog.getOpenFileName(
					self.mainwindow,
					". Datei öffnen",
					defaultfilepath,
					additionalfilefilter
				)
				if string_is_empty(additional_filepath):
					invalid_additional = True
					break
				else:
					if last_additionalfiles is None:
						last_additionalfiles = []
					last_additionalfiles.append(additional_filepath)

			if invalid_additional:
				return

		if self.last_additionalfiles is not None:
			self.last_additionalfiles.clear()

		self.last_additionalfiles = last_additionalfiles
		self.yamlSet(lastchannel_filepath, "main", "lastchannel_filepath")
		self.last_filename = last_filename
		self.pluginmodule = pluginmodule

		self.model.reset()
		self.model.load(self.pluginmodule, self.last_filename, self.last_additionalfiles)
		self.model.signalStopLoading.connect(self.onStopLoading)
		self.mainwindow.setWindowTitle(self.last_filename)

	def onStopLoading(self, total_item_count, title_and_error):
		if not is_empty_sequence(title_and_error):
			tl = len(title_and_error)
			messagebox(
				self.prevmessagebox,
				title_and_error[0] if tl > 1 else "Fehler",
				title_and_error[1] if tl > 1 else title_and_error[0],
				title_and_error[2] if tl > 2 else None,
				title_and_error[3] if tl > 3 else None
			)
		else:
			if not self.searchdialog.modelWasSet():
				self.searchdialog.setModel(self.model)

			self.ui.labelStatus1.setText("Gesamt: {}".format(total_item_count))
			self.ui.actionSaveAs.setEnabled(True)
			self.ui.actionSave.setEnabled(True)
			self.ui.actionSearch.setEnabled(True)

	def getPluginModule(self, index):
		p = None
		for plugin in self.plugins:
			if plugin.getRegistryIndex() == index:
				p = plugin
				break
		return p

	def onDeleteItems(self):
		self.model.deleteSelectedItems()

	def deleteDoubleItem(self):
		self.model.deleteLastDoubles()
