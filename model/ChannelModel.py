# from os import linesep
from typing import List, Any

from PyQt5.QtCore import Qt, QModelIndex, QVariant, QAbstractItemModel, \
	QIODevice, QByteArray, QMimeData, QDataStream, QItemSelection, \
	QItemSelectionModel, pyqtSignal, pyqtSlot, QEvent, QObject, QTimer
from PyQt5.QtWidgets import QFileDialog, QAbstractItemView

from PyQt5.QtCore import pyqtSlot
# from PyQt5.QtWidgets import QStyle
# from pprint import PrettyPrinter
from gui.MainWindow import Ui_MainWindow
from gui.MainWindowWrapper import MainWindowWrapper
from gui.TreeViewDropProxyStyle import TreeViewDropProxyStyle
from lib.Helpers import is_dict, filefilter_to_extension, filepath_verify_extension, detect_file_encoding_str, \
	string_is_empty, get_reformatted_exception, is_empty_sequence
from lib.QTHelpers import messagebox
from model import Channel
from model.Channel import Channel
from model.ChannelFieldList import ChannelFieldList
from gui.ChannelLoaderSaverThread import ChannelLoaderSaver
from gui.ContextProcessor import ContextProcessor


class ChannelModel(QAbstractItemModel):

	MIMETYPE = "application/x-qabstractitemmodeldatalist"

	cachedmessagebox = None

	messageboxwidth = 400

	encoding = None
	""":type:str"""

	channelfields = None
	""":type:ChannelFieldList"""

	initialized = None
	""":type:bool"""

	# channels = None
	# """:type:list[Channel]"""

	mainui = None
	""":type: Ui_MainWindow"""

	treeview = None
	""":type:QTreeView"""

	progressbar = None
	""":type:QProgressBar"""

	rootitem = None

	maxsortlevels = 1
	""":type:int"""

	contextmenu = None
	""":type:ChannelModelCtx"""

	total_item_count = None
	""":type:int"""

	selected_drop_indicies_parent = None
	""":type:QModelIndex"""

	signalStopLoading = pyqtSignal(int, list)
	""":type:pyqtSignal"""

	on_delete_channel = pyqtSlot(Channel)
	""":type:pyqtSlot"""

	def __init__(self, mainui: Ui_MainWindow, maxsortlevels: int = None):
		super(ChannelModel, self).__init__(mainui.treeView)
		# QAbstractItemModel.__init__(self)

		if maxsortlevels is not None:
			self.maxsortlevels = maxsortlevels

		self.mainui = mainui
		self.treeview = mainui.treeView
		self.progressbar = mainui.progressBar
		self.contextmenu = ContextProcessor(self)

		self.treeview.setContextMenuPolicy(Qt.CustomContextMenu)
		self.treeview.customContextMenuRequested.connect(self.contextmenu.contextMenuOpen)
		self.treeview.setModel(self)
		self.treeview.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.treeview.setSelectionBehavior(QAbstractItemView.SelectRows)
		self.treeview.setDragEnabled(True)
		self.treeview.setDropIndicatorShown(True)
		self.treeview.setAcceptDrops(True)
		self.treeview.setDragDropMode(QAbstractItemView.InternalMove)
		self.treeview.setRootIsDecorated(True)
		self.treeview.setStyle(TreeViewDropProxyStyle())
		self.treeview.setSelectionBehavior(QAbstractItemView.SelectRows)
		self.initialized = False

	def __str__(self):
		s = ""
		for i in self.channelfields:
			s += str(i) + "\n"
		return s

	def eventFilter(self, widget: QObject, event: QEvent):
		if event.type() == QEvent.KeyPress:
			if event.key() == Qt.Key_Delete:
				self.deleteSelectedItems()
				return True
		return False

	def reset(self):
		try:
			self.beginResetModel()
			if self.rootitem is not None:
				cc = self.rootitem.childchannels
				for ccc in cc:  # type: Channel
					ccc.clear()
				self.rootitem.clear()
				self.rootitem = None
			if self.channelfields is not None:
				self.channelfields.clear()
				self.channelfields = None
			self.total_item_count = 0
			self.initialized = False
			self.encoding = None
			self.endResetModel()
		except Exception as e:
			print(get_reformatted_exception("", e))

	def setMainUIDisabled(self, state: bool):
		self.mainui.treeView.setDisabled(state)
		self.mainui.toolBar.setDisabled(state)
		self.mainui.menubar.setDisabled(state)

	def saveAs(self, parentwindow: MainWindowWrapper, pluginmodule: dict, last_saveas_folderpath: str, last_additionalfiles: List[str]):
		filepath, filefilter = QFileDialog.getSaveFileName(
			parentwindow,
			"Kanallisten-Hauptdatei speichern unter...",
			last_saveas_folderpath,
			pluginmodule["filefilter"])

		if string_is_empty(filepath):
			return

		ext = filefilter_to_extension(filefilter)

		if not filepath_verify_extension(filepath, ext):
			filepath += "." + ext

		newadditionalfiles = []

		if "additionalfilefilter" in pluginmodule and not is_empty_sequence(pluginmodule["additionalfilefilter"]):

			additionalfilefilters = pluginmodule["additionalfilefilter"]
			additionalfiles_valid = True

			# Todo: Whats up with additionalfilefilter?
			for additionalfilefilter in additionalfilefilters:
				additionalfile, additionalfilefilter = QFileDialog.getSaveFileName(
					parentwindow,
					"Kanallisten-Nebendatei speichern unter...",
					last_saveas_folderpath,
					additionalfilefilter)  # pluginmodule["filefilter"])
				if string_is_empty(additionalfile):
					additionalfiles_valid = False
					break

				ext = filefilter_to_extension(additionalfilefilter)
				if not filepath_verify_extension(additionalfile, ext):
					additionalfile += "." + ext
				newadditionalfiles.append(additionalfile)
			if not additionalfiles_valid:
				return
		self._save(pluginmodule, filepath, last_additionalfiles, newadditionalfiles)

	def save(self, pluginmodule: dict, filename: str, additionalfiles: List[str]):
		self._save(pluginmodule, filename, additionalfiles, additionalfiles)

	def _save(self, pluginmodule: dict, filepath: str, last_additionalfiles: List[str], additionalfiles: List[str]):
		cl = ChannelLoaderSaver(
			self,
			filepath,
			last_additionalfiles,
			additionalfiles,
			pluginmodule,
			pluginmodule["plugin"].writeFile
		)
		cl.signalBeforeInit.connect(lambda: self.layoutAboutToBeChanged.emit())
		cl.signalAfterInit.connect(lambda: self.layoutChanged.emit())
		cl.signalStart.connect(self.onChannelLoaderStartLoading)
		cl.signalStop.connect(self.onChannelLoaderStopLoading)
		cl.signalProgressItem.connect(self.onChannelLoaderProgressItem)
		cl.start()

	def load(self, pluginmodule: dict, filepath: str, additionalfiles: List[str]):

		try:

			if "detectencoding" not in pluginmodule or pluginmodule["detectencoding"] is True:
				self.encoding = detect_file_encoding_str(filepath)
				if string_is_empty(self.encoding):
					raise (Exception("Datei-Encoding konnte nicht festgestellt werden"))

			if not is_dict(pluginmodule) or pluginmodule["name"] == "Group":
				raise (Exception("Dateiendung unbekannt"))

			if self.channelfields is None:
				self.channelfields = ChannelFieldList.createChannelFieldListByChannelType(pluginmodule)
			else:
				self.channelfields = self.channelfields.reInitFromChannelType(pluginmodule)

			self.rootitem = Channel("Alle", True, pluginmodule, self.channelfields)

			cl = ChannelLoaderSaver(
				self,
				filepath,
				additionalfiles,
				None,
				pluginmodule,
				pluginmodule["plugin"].readFile
			)
			cl.signalBeforeInit.connect(lambda: self.layoutAboutToBeChanged.emit())
			cl.signalAfterInit.connect(lambda: self.layoutChanged.emit())
			cl.signalStart.connect(self.onChannelLoaderStartLoading)
			cl.signalStop.connect(self.onChannelLoaderStopLoading)
			cl.signalProgressItem.connect(self.onChannelLoaderProgressItem)
			cl.start()

		except Exception as e:
			self.showMessageboxException("in ChannelModel.load()", e)

	@pyqtSlot(int)
	def onChannelLoaderStartLoading(self, count):
		self.total_item_count = count
		self.progressbar.show()
		self.progressbar.reset()
		self.progressbar.setMaximum(count)

	@pyqtSlot(list)
	def onChannelLoaderStopLoading(self, title_and_error: List[str]):
		self.progressbar.hide()
		self.signalStopLoading.emit(self.total_item_count, title_and_error)

	@pyqtSlot(tuple)
	def onChannelLoaderProgressItem(self, args):
		self.progressbar.setValue(args[0])

		argslen = len(args)

		if argslen > 1:
			arg1ok = args[1] is not None and type(args[1]) is Channel
			arg2ok = False
			if argslen > 2:
				arg2ok = args[2] is not None and type(args[2]) is Channel
			if arg1ok and not arg2ok:
				self.rootitem.appendChild(args[1])
			elif arg1ok and arg2ok:
				args[2].setParent(args[1])
				args[1].appendChild(args[2])

	def showMessageboxException(self, pretext: str, e: Exception):
		self.cachedmessagebox = messagebox(
			self.cachedmessagebox,
			"Fehler",
			pretext,
			None,
			get_reformatted_exception(None, e),
			False, 500
		)

	def showMessagebox(self, title, intro, text, detailed_text=None, show_cancel=False):
		self.cachedmessagebox = messagebox(
			self.cachedmessagebox,
			title,
			intro,
			text,
			detailed_text,
			show_cancel,
			self.messageboxwidth
		)

	def selectedCategoryCount(self):
		indicies = self.treeview.selectionModel().selectedIndexes()
		count = None
		for index in indicies:
			if index.column() == 0:
				if indicies[0].parent() is None or indicies[0].parent().internalPointer() is None:
					if count is not None:
						count = None
						break
					parent = indicies[0].internalPointer()
					count = parent.childCount()
				else:
					count = None
					break
		return count

	def allChannelCount(self):
		return self.total_item_count

	def rowCount(self, parent: QModelIndex = ...):
		if parent.isValid():
			return parent.internalPointer().childCount()
		if self.rootitem is None:
			return 0
		return self.rootitem.childCount()

	def columnCount(self, parent=None, *args, **kwargs):
		if self.channelfields is None:
			return 0
		return self.channelfields.countVisible()

	def headerData(self, column: int, orientation: Qt.Orientation, role: int = None):
		if orientation == Qt.Horizontal:
			if role == Qt.DisplayRole and self.channelfields is not None:
				channelfield = self.channelfields.getFieldByColumnIndex(column)
				if channelfield is not None:
					return channelfield.fieldcaption
		elif orientation == Qt.Vertical:
			return column
		return QVariant()

	def parent(self, child: QModelIndex):
		try:
			if child is not None and child.isValid():
				parentitem = child.internalPointer().parentItem()
				if parentitem is not None and parentitem != self.rootitem:
					return QAbstractItemModel.createIndex(self, parentitem.row(), 0, parentitem)
			return QModelIndex()
		except Exception as e:
			self.showMessageboxException("in ChannelModel.parent()", e)

	def index(self, row: int, column: int, parent: QModelIndex = None):
		if parent is None or not QAbstractItemModel.hasIndex(self, row, column, parent):
			return QModelIndex()

		if not parent.isValid():
			parentitem = self.rootitem
		else:
			parentitem = parent.internalPointer()

		child = parentitem.child(row)

		if child is not None:
			return QAbstractItemModel.createIndex(self, row, column, child)
		else:
			QModelIndex()

	def setData(self, index: QModelIndex, value: Any, role: int=None):
		if role is not None and role == Qt.EditRole and index is not None and index.isValid():
			rowindex = index.row()
			columnindex = index.column()
			if rowindex > -1 and columnindex == 0:
				c = index.internalPointer()
				""":type: Channel"""
				if c.parentchannel != self.rootitem:
					channelfield = self.channelfields.getFieldByName("name")
					if channelfield is not None:
						index.internalPointer().setDataByField(channelfield, value)
						return True
		return False

	def data(self, index: QModelIndex, role: int = None) -> Any:
		if index.isValid() and self.channelfields is not None:
			if role == Qt.DisplayRole or role == Qt.EditRole:
				col = index.column()
				return index.internalPointer().data(col)
		return QVariant()

	def indexRootLevel(self, column: int):
		return self.index(self.rootitem.row(), column)

	def indexFirstLevel(self, parentchannel: Channel, column: int, open: bool=True):
		# firstcol_index = self.index(parentchannel.row(), 0, self.indexRootLevel(0))
		# if not self.treeview.isExpanded(firstcol_index):
		# 	self.treeview.expand(firstcol_index)
		return self.index(parentchannel.row(), column, self.indexRootLevel(column))

	def indexSecondLevel(self, subchannel: Channel, column: int, open: bool=True):
		return self.index(subchannel.row(), column, self.indexFirstLevel(subchannel.parentchannel, column))

	def selectItem(self, channel: Channel):
		if channel is not None:
			m = self.treeview.selectionModel()
			m.clearSelection()
			first_sel_index = self.indexSecondLevel(channel, 0)
			self.treeview.scrollTo(first_sel_index)

			sel = QItemSelection(
				first_sel_index,
				self.indexSecondLevel(channel, self.channelfields.countVisible() - 1)
			)
			m.select(sel, QItemSelectionModel.SelectCurrent)

	@pyqtSlot(Channel)
	def deleteChannel(self, channel: Channel):
		if channel is not None and channel.parentchannel is not None:
			self.setMainUIDisabled(True)
			try:
				p = channel.parentchannel
				""":type: Channel"""

				pi = self.index(p.row(), 0, self.indexRootLevel(0))
				r = p.childchannels.index(channel)
				self.beginRemoveRows(pi, r, r)
				p.removeChildByIndex(r)
				self.endRemoveRows()

			except Exception as e:
				self.showMessageboxException("in ChannelModel.deleteChannel()", e)
			self.setMainUIDisabled(False)

	def deleteEmptyNames(self, parentnode: Channel):
		self.setMainUIDisabled(True)

		try:
			to_delete = []
			for childchannel in parentnode.childchannels:
				name = childchannel.getValueByFieldName("name")
				if string_is_empty(name, False):
					to_delete.append(childchannel)

			self.layoutAboutToBeChanged.emit()

			while len(to_delete) > 0:
				parentnode.removeChildByChannel(to_delete[0])
				to_delete.remove(to_delete[0])

			self.layoutChanged.emit()
		except Exception as e:
			self.showMessageboxException("in ChannelModel.deleteEmptyNames()", e)

	def deleteLastDoubles(self, parentnode: Channel):
		self.setMainUIDisabled(True)
		try:

			progs = {}

			for childchannel in parentnode.childchannels:
				name = childchannel.getValueByFieldName("name")
				if name in progs:
					progs[name].append(childchannel)
				else:
					progs[name] = [childchannel]

			self.layoutAboutToBeChanged.emit()

			for progvalues in progs.values():
				for index, it in enumerate(progvalues):
					if index > 0:
						parentnode.childchannels.remove(it)

			self.layoutChanged.emit()
		except Exception as e:
			self.showMessageboxException("in ChannelModel.deleteLastDoubles()", e)
		self.setMainUIDisabled(False)

	def deleteSelectedItems(self):
		self.setMainUIDisabled(True)
		try:
			selmodel = self.treeview.selectionModel()
			""":type: QItemSelectionModel"""
			sel = selmodel.selectedIndexes()
			d = {}

			if len(sel) > 0:
				prevFirst = sel[0].sibling(sel[0].row()-1, 0)
				prevLast = sel[0].sibling(sel[1].row()-1, self.channelfields.countVisible()-1)

			for selitem in sel:
				col = selitem.column()
				if col == 0:
					row = selitem.row()
					parent = selitem.parent()

					if parent is not None and parent.internalPointer() is not None:
						if parent in d:
							d[parent].append(row)
						else:
							d[parent] = [row]

			if len(d) > 0:
				for parent, rows in d.items():
					rows.reverse()
					for row in rows:
						self.beginRemoveRows(parent, row, row)
						parent.internalPointer().removeChildByIndex(row)
						self.endRemoveRows()

			selmodel.select(QItemSelection(
				prevFirst,
				prevLast),
				QItemSelectionModel.Select
			)

			QTimer.singleShot(200, lambda: self.treeview.setFocus())

		except Exception as e:
			self.showMessageboxException("in ChannelModel.deleteSelectedItems()", e)

		self.setMainUIDisabled(False)

	def flags(self, index) -> Qt.ItemFlags:
		if not index.isValid():
			return Qt.ItemIsEnabled  # Qt.NoItemFlags
		defflags = QAbstractItemModel.flags(self, index)
		col = index.column()
		if col == 0:
			defflags |= Qt.ItemIsEditable
		return defflags | Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled | Qt.ItemIsSelectable

	def supportedDropActions(self):
		return Qt.CopyAction | Qt.MoveAction

	def supportedDragActions(self):
		return Qt.CopyAction | Qt.MoveAction

	def mimeData(self, indicies: Any):
		mimedata = QMimeData()
		encodedData = QByteArray()
		stream = QDataStream(encodedData, QIODevice.WriteOnly)
		lastparent = None
		lastrow = None

		for idx, index in enumerate(indicies):
			if lastrow is not None and lastrow == index.row():
				continue
			if index.isValid():
				if lastparent is None:
					lastparent = index.parent()
					self.selected_drop_indicies_parent = lastparent
				else:
					if index.parent() != lastparent:
						self.selected_drop_indicies_parent = None
						break
				stream.writeInt32(index.row())
				lastrow = index.row()

		mimedata.setData(ChannelModel.MIMETYPE, encodedData)
		return mimedata

	def decodeMimeData(self, mimedata: QMimeData):
		items = None
		if mimedata.hasFormat(ChannelModel.MIMETYPE):
			items = []
			modelbytearray = mimedata.data(ChannelModel.MIMETYPE)
			ds = QDataStream(modelbytearray)
			while not ds.atEnd():
				row = ds.readInt32()
				if items is None:
					items = []
				items.append(row)
			items.sort(reverse=True)
		return items

	def canDropMimeData(
			self,
			mimedata: QMimeData,
			action: Qt.DropAction,
			droprow: int,
			dropcolumn: int,
			dropindex: QModelIndex
	):
		if self.selected_drop_indicies_parent is None or dropindex is None:
			return False
		if dropindex.parent() is None or dropindex.parent().internalPointer() is None:
			new_dropindex = dropindex.internalPointer()
			if new_dropindex is None:
				return False
			if dropindex != self.selected_drop_indicies_parent:
				return False
			return True
		return False

	def dropMimeData(
			self,
			mimedata_indicies: QMimeData,
			action: Qt.DropAction,
			droprow: int,
			dropcolumn: int,
			parentindex: QModelIndex
	):
		mimedata_indicies = self.decodeMimeData(mimedata_indicies)

		dropchannels = []
		""":type:list[Channel]"""

		parent = parentindex.internalPointer()
		""":type:Channel"""

		mdl = len(mimedata_indicies)
		indexend = mimedata_indicies[0]
		indexstart = mimedata_indicies[mdl - 1]

		after = droprow > indexend
		before = (droprow - 1) < indexstart
		middle = after is False and before is False

		for mimedata_index in mimedata_indicies:
			self.beginRemoveRows(parentindex, mimedata_index, mimedata_index)
			dropchannels.append(parent.removeChildByIndex(mimedata_index))
			self.endRemoveRows()

		dropchannels.reverse()

		droprowmod = droprow

		if middle:
			for idx, mimedataitem in enumerate(mimedata_indicies):
				if mimedataitem < droprow:
					droprowmod -= mdl - idx
					break
		elif after:
			droprowmod -= mdl

		mimedata_indicies.reverse()

		for idx, dropchannel in enumerate(dropchannels):
			dropidx = droprowmod + idx
			self.beginInsertRows(parentindex, dropidx, dropidx)
			parent.insertChild(dropchannel, dropidx)
			self.endInsertRows()

		self.treeview.clearSelection()

		selmodel = self.treeview.selectionModel()

		newselection = QItemSelection(
			self.index(droprowmod, 0, parentindex),
			self.index(droprowmod + mdl - 1, self.channelfields.countVisible() - 1, parentindex)
		)

		selmodel.select(newselection, QItemSelectionModel.SelectCurrent)

		return True
