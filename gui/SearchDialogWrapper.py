from typing import Any

from PyQt5.Qt import Qt, QItemSelectionModel, QModelIndex, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtCore import QTimer, QObject

from gui.DialogWrapper import DialogWrapper
from gui.SearchDialog import Ui_SearchDialog
from gui.SearchThread import SearchThread

from model.Channel import Channel
from model.ChannelModel import ChannelModel
from lib.Helpers import get_reformatted_exception
from lib.QTHelpers import removeListWidgetItemByIndex


class SearchDialogWrapper(QObject):

	uisearchdialog = None
	""":type: Ui_HelpDialog"""

	searchdialog = None

	lastlink = None
	""":type: List[str]"""

	cached_tabs = None
	""":type: SortedDict"""  # {link:str: Tuple(sectionname:str, tab:QTextBrowser)}

	model = None
	""":type: ChannelModel"""

	model_was_set = None
	""":type: bool"""

	app = None

	signal_mainwin_deletechannel = pyqtSignal(Channel)

	def __init__(self, app):
		super(SearchDialogWrapper, self).__init__()
		self.app = app
		self.uisearchdialog = Ui_SearchDialog()
		self.searchdialog = DialogWrapper(self.uisearchdialog)
		self.uisearchdialog.buttonBox.clicked.connect(self.onButtonClickedOk)
		self.uisearchdialog.buttonStartSearch.clicked.connect(self.onButtonClickedSearchStart)
		self.uisearchdialog.listWidgetResults.itemDoubleClicked.connect(self.onResultListDoubleClicked)
		self.uisearchdialog.listWidgetResults.selectionModel().currentRowChanged.connect(self.onResultListRowChanged)
		self.searchdialog.setModal(True)
		self.uisearchdialog.progressBar.hide()
		self.model_was_set = False

	def test(self):
		pass

	def setModel(self, model: ChannelModel):
		try:
			if self.model_was_set is False:
				self.model = model
				self.signal_mainwin_deletechannel.connect(self.model.deleteChannel)
				self.uisearchdialog.buttonDeleteResults.clicked.connect(self.onButtonClickedDeleteResult)

			self.model_was_set = True

		except Exception as e:
			print(get_reformatted_exception(e))

	def modelWasSet(self):
		return self.model_was_set

	def show(self):
		self.searchdialog.show()

	def onResultListRowChanged(self):
		if not self.uisearchdialog.buttonDeleteResults.isEnabled():
			self.uisearchdialog.buttonDeleteResults.setEnabled(True)

	def onButtonClickedDeleteResult(self):
		sm = self.uisearchdialog.listWidgetResults.selectionModel()
		""":type: QItemSelectionModel"""

		index = sm.currentIndex()
		""":type: QModelIndex"""

		try:
			if index.isValid():
				item = self.uisearchdialog.listWidgetResults.itemFromIndex(index)
				""":type: QListWidgetItem"""
				channel = item.data(Qt.UserRole)
				item.setData(Qt.UserRole, None)
				if channel is not None:
					self.signal_mainwin_deletechannel.emit(channel)

					removeListWidgetItemByIndex(self.uisearchdialog.listWidgetResults, index)

					r = index.row()

					sibling = index.sibling(r, 0)

					sel = self.uisearchdialog.listWidgetResults.selectionModel()
					""":type: QItemSelectionModel"""

					sel.setCurrentIndex(sibling, QItemSelectionModel.Select)

					self.uisearchdialog.listWidgetResults.setFocus()

					if self.uisearchdialog.listWidgetResults.count() == 0:
						self.uisearchdialog.buttonDeleteResults.setEnabled(False)

		except Exception as e:
			self.model.showMessageboxException("in SearchDialogWrapper.onButtonClickedDeleteResult()", e)

	def onSearchStart(self, item_count):
		self.uisearchdialog.listWidgetResults.clear()
		self.uisearchdialog.progressBar.show()
		self.uisearchdialog.progressBar.reset()
		self.uisearchdialog.progressBar.setMaximum(item_count)

	def onSearchProgress(self, item_index: int, data: Any):
		# listwidget = self.uisearchdialog.listWidgetResults
		# """:type: QListWidget"""
		self.uisearchdialog.progressBar.setValue(item_index)
		if data is not None:
			channel = data[0]
			field = data[1]
			i = QListWidgetItem("Sender: '{}' in Feld '{}'".format(channel.getValueByFieldName("name"), field.fieldcaption))
			i.setData(Qt.UserRole, channel)
			self.uisearchdialog.listWidgetResults.addItem(i)

	def onSearchStop(self):
		self.uisearchdialog.progressBar.hide()

	def onResultListDoubleClicked(self, item: QListWidgetItem):
		channel = item.data(Qt.UserRole)
		if channel is not None:
			self.model.selectItem(channel)

	def onButtonClickedOk(self):
		self.searchdialog.close()

	def onButtonClickedSearchStart(self):
		s = SearchThread(
			self.model.rootitem,
			self.uisearchdialog.lineEditSearch.text(),
			self.uisearchdialog.checkboxCase.isChecked(),
			self.uisearchdialog.checkboxWholeWord.isChecked(),
			lambda item_count: self.onSearchStart(item_count),
			lambda item_index, data: self.onSearchProgress(item_index, data),
			lambda: self.onSearchStop()
		)
		s.start()
