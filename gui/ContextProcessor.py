from enum import Enum
from typing import Tuple, Any
from PyQt5.Qt import QAction, QActionGroup, QMenu
from lib.Helpers import is_empty_sequence


class MenuActionType(Enum):
	Undefined = 1
	ReverseCheckbox = 2
	SortCategory = 3
	DeleteEmpty = 4
	DeleteDouble = 5
	Delete = 6


class ContextProcessor:

	treeTopLevelContexts = None
	""":type:dict[Channel,QMenu]"""

	channelmodel = None

	mainui = None
	""":type: Ui_MainWindow"""

	def __init__(self, channelmodel):
		self.channelmodel = channelmodel

	def sortSublist(self, parent_channel, sort_channelfield, startindex, stopindex, reverse):
		sublist = parent_channel.childchannels[startindex:stopindex]
		sublist.sort(key=lambda channel: channel.values[sort_channelfield], reverse=reverse)
		parent_channel.childchannels[startindex:stopindex] = sublist

	@staticmethod
	def determineActionType(menuaction: QAction):
		if menuaction is not None and not menuaction.isSeparator() and \
				menuaction.menu() is None and menuaction.data() is not None:
			d = menuaction.data()
			if not is_empty_sequence(d):
				if d[0] == "dd":
					return MenuActionType.DeleteDouble
				elif d[0] == "de":
					return MenuActionType.DeleteEmpty
				elif d[0] == "r":
					return MenuActionType.ReverseCheckbox
				elif d[0] == "s":
					return MenuActionType.SortCategory
				elif d[0] == "d":
					return MenuActionType.Delete
		return MenuActionType.Undefined

	def contextMenuNewSortActions(self, level, caption, parentmenu, parentnode):
		channelfields = self.channelmodel.channelfields
		if channelfields is not None:
			sortmenu = QMenu(caption, parentmenu)
			c = channelfields.countAll()
			actiongroup = QActionGroup(sortmenu)
			actiongroup.setExclusive(True)

			for i in range(0, c):
				cf = channelfields.getFieldByColumnIndex(i)

				if cf.visible is True and cf.sortable:
					action = QAction(cf.fieldcaption, actiongroup, checkable=True)
					action.setData(["s", level, cf, parentnode, parentmenu, sortmenu])
					actiongroup.addAction(action)
					sortmenu.addAction(action)

			reverseaction = QAction("Rückwärts", sortmenu, checkable=True)
			reverseaction.setData(["r", sortmenu])
			sortmenu.addAction(reverseaction)

			return sortmenu
		return None

	def contextMenuGetSubLevel(self, nodes):
		menu = QMenu()
		qa = QAction("Löschen", menu)
		qa.setData(["d"])
		menu.addAction(qa)
		menu.triggered.connect(self.contextMenuActionTriggered)
		return menu

	def contextMenuGetTopLevel(self, node) -> Tuple[Any]:
		"""

		:param node: The top-level-node on which the contextmenu was called
		:return: A tuple containing a bool for the 1st, which states if the
		returned menu was created new (for another top-level-node).
		The 2nd item of the tuple will be the QMenu context-item itself
		:rtype: Tuple(bool, QMenu)
		"""
		if node is None:
			return False, None

		if self.treeTopLevelContexts is None:
			self.treeTopLevelContexts = {}

		if node in self.treeTopLevelContexts:
			return False, self.treeTopLevelContexts[node]

		name = node.getValueByFieldName("name")
		menu = QMenu()

		qa = QAction(name, menu)
		qa.setEnabled(False)
		menu.addAction(qa)

		menu.addSeparator()

		qaempty = QAction("Kanäle mit leeren Namen löschen", menu)
		qaempty.setData(["de", node])
		menu.addAction(qaempty)

		menu.addSeparator()

		qadouble = QAction("Doppelte löschen", menu)
		qadouble.setData(["dd", node])
		menu.addAction(qadouble)

		menu.addSeparator()

		originalparent = self.contextMenuNewSortActions(0, "1. Sortierung", menu, node)
		previousparent = None

		menu.addMenu(originalparent)

		for i in range(1, self.channelmodel.maxsortlevels):
			submenucaption = str(i + 1) + ". Sortierung"
			submenu = self.contextMenuNewSortActions(
				i,
				submenucaption,
				originalparent if previousparent is None else previousparent,
				node
			)

			if previousparent is None:
				originalparent.addMenu(submenu)
			else:
				previousparent.addMenu(submenu)

			previousparent = submenu

		self.treeTopLevelContexts[node] = menu

		menu.triggered.connect(self.contextMenuActionTriggered)

		return True, menu

	def contextMenuAreParentSortCategorySet(self, parentmenu: QMenu):

		hasSelection = False
		isSortSubmenu = False

		for a in parentmenu.actions():
			actionmenutype = ContextProcessor.determineActionType(a)

			if actionmenutype is MenuActionType.Undefined:
				break

			if actionmenutype is MenuActionType.SortCategory:
				isSortSubmenu = True
				hasSelection = a.isChecked()
				if hasSelection is True:
					break

		if isSortSubmenu:
			return True

		if hasSelection:
			return self.contextMenuAreParentSortCategorySet(parentmenu.parent())

		return False

	def contextMenuActionTriggered(self, action: QAction):

		d = action.data()

		reverse = None
		sortlevel = None
		channelfield = None
		parentnode = None
		parentmenu = None

		if is_empty_sequence(d):
			return None

		actionmenutype = ContextProcessor.determineActionType(action)

		if actionmenutype is MenuActionType.DeleteDouble:
			parentnode = action.data()[1]
			self.channelmodel.deleteLastDoubles(parentnode)
		elif actionmenutype is MenuActionType.DeleteEmpty:
			parentnode = action.data()[1]
			self.channelmodel.deleteEmptyNames(parentnode)
		elif actionmenutype is MenuActionType.Delete:
			self.channelmodel.deleteSelectedItems()
		elif actionmenutype is MenuActionType.ReverseCheckbox:
			self.channelmodel.setMainUIDisabled(True)

			# Reverse-order-checkbox was selected
			reverse = action.isChecked()

			# Find current selected sort-category-radiobutton in menu
			sortmenu = d[1]

			for action in sortmenu.actions():
				ds = action.data()
				if ContextProcessor.determineActionType(action) is MenuActionType.SortCategory:
					if action.isChecked():
						sortlevel = ds[1]
						channelfield = ds[2]
						parentnode = ds[3]
						parentmenu = ds[4]
						break

		elif actionmenutype is MenuActionType.SortCategory:
			self.channelmodel.setMainUIDisabled(True)

			# Sort-category-radiobutton was selected
			sortlevel = d[1]
			""":type:int"""

			channelfield = d[2]
			""":type:ChannelField"""

			parentnode = d[3]
			""":type:Channel"""

			parentmenu = d[4]
			""":type:QMenu"""

			sortmenu = d[5]
			""":type:QMenu"""

			if sortmenu is not None:
				for action in sortmenu.actions():
					if ContextProcessor.determineActionType(action) is MenuActionType.ReverseCheckbox:
						reverse = action.isChecked()
						break

		if sortlevel is None or channelfield is None or parentmenu is None or \
			parentnode is None or reverse is None or sortmenu is None:
			self.channelmodel.setMainUIDisabled(False)
			return None

		if actionmenutype is MenuActionType.ReverseCheckbox or \
			actionmenutype is MenuActionType.SortCategory:
			if reverse is None:
				reverse = False
				for action in sortmenu.actions():
					if ContextProcessor.determineActionType(action) is MenuActionType.ReverseCheckbox:
						reverse = action.isChecked()
						break

			if sortlevel == 0:
				parentnode.childchannels.sort(key=lambda channel: channel.values[channelfield], reverse=reverse)
			else:
				if not self.contextMenuAreParentSortCategorySet(parentmenu):
					action.setChecked(False)
					self.channelmodel.showMessagebox(
						"Fehler",
						"in ChannelModelCtx.contextMenuActionTriggered()",
						"Bitte erst mittels eines übergeordneten Menüs sortieren"
					)

				parent_sortfield = None

				for action in parentmenu.actions():
					if not is_empty_sequence(action.data()) and action.isChecked():
						pd = action.data()
						parent_sortfield = pd[2]
						break

				if parent_sortfield is not None:

					c = len(parentnode.childchannels)
					lastitem = None
					startindex = 0

					for i in range(0, c):
						channel = parentnode.childchannels[i]
						currentitem = channel.getValueByField(parent_sortfield)

						if i == c-1:
							self.sortSublist(parentnode, channelfield, startindex, i + 1, reverse)

						if lastitem is not None:
							if currentitem != lastitem:
								self.sortSublist(parentnode, channelfield, startindex, i, reverse)
								startindex = i

						lastitem = currentitem

		self.channelmodel.setMainUIDisabled(False)

	def contextMenuOpen(self, position):
		indexes = self.channelmodel.treeview.selectedIndexes()

		if indexes is None or len(indexes) == 0:
			return None

		lastindex = None
		indicies = []

		for index in indexes:
			row = index.row()
			if lastindex is None:
				lastindex = row
				indicies.append(index)
			elif lastindex != row:
				lastindex = row
				indicies.append(index)

		if indicies is not None:

			c = len(indicies)

			if c == 0:
				return None

			if c == 1 and indicies[0].parent() is None or not indicies[0].parent().isValid():
				# Click on one of the top level nodes (single selection)
				node = indicies[0].internalPointer()
				is_new_menu, menu = self.contextMenuGetTopLevel(node)
				node.pluginmodule["plugin"].addToTopLevelContextMenu(is_new_menu, indicies[0].internalPointer(), menu)
				menu.exec(self.channelmodel.treeview.viewport().mapToGlobal(position))
			else:
				menu = self.contextMenuGetSubLevel(indicies)
				menu.exec(self.channelmodel.treeview.viewport().mapToGlobal(position))