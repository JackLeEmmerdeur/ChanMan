from abc import ABCMeta, ABC, abstractmethod
from typing import List, Dict, Any
from model.ChannelField import ChannelField
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMenu
from model.Channel import Channel
from six import add_metaclass
from collections import OrderedDict


@add_metaclass(ABCMeta)
class ITVPlugin:
	# __metaclass__ = ABCMeta
	plugindict = None

	@abstractmethod
	def getRegistryIndex(self) -> int:
		"""
		Has to correspond to the index of the plugin within PluginRegistry.plugins

		:return:
		"""
		raise NotImplementedError

	@abstractmethod
	def getFieldCaptions(self) -> List[str]:
		"""
		Returns the column-captions in the treeview

		:return:
		"""
		raise NotImplementedError

	@abstractmethod
	def getFieldNames(self) -> List[str]:
		"""
		Returns the internal names of the fields for use within
		Channel.getFieldByName() or Channel.getValueByFieldName()

		:return:
		"""
		raise NotImplementedError

	@abstractmethod
	def getFieldVisibility(self) -> List[bool]:
		"""
		Returns the visiblity of the fields within the treeview

		:return:
		"""
		raise NotImplementedError

	@abstractmethod
	def getFieldTypes(self) -> List[Any]:
		"""
		Returns the types of the fields.
		Every item in the list has to contain a value of type ChannelFieldType

		:return:
		"""
		raise NotImplementedError

	@abstractmethod
	def getFieldSortability(self) -> List[bool]:
		"""
		Returns a list of which every item states if a column within the treeview can be sorted

		:return:
		"""
		raise NotImplementedError

	@abstractmethod
	def getFileColumnIndicies(self) -> List[int]:
		"""
		Returns the positions of every column.

		:return: Use -1 for an item if the fieldvisibility (see getFieldVisibility()) is False
		"""
		raise NotImplementedError

	@abstractmethod
	def getTreeCategories(self) -> OrderedDict:
		"""
		Returns a OrderedDict.
		The keys stand for the caption of a top category treeview-item.
		Every key contains a dict as a value.
		This dict contains string-keys and arbritrary typed values that
		represent data brought along with the treeview-item

		:return:
		"""
		raise NotImplementedError

	@abstractmethod
	def addToTopLevelContextMenu(self, is_new_menu: bool, parentchannel: Channel, ctx: QMenu) -> None:
		"""
		A hook method which gets called before the context-menu of the treeview is created.
		You can therefore add own items for the plugin into the ctx-parameter.

		:param is_new_menu: States if ctx is a cached menu, or if it is freshly build
		:param parentchannel: Which top-level-treeview-item (category) was right-clicked on
		:param ctx: The contextmenu
		:return:
		"""
		raise NotImplementedError

	# writeFile()
	@abstractmethod
	def writeFile(
		self,
		filepath: str,
		encoding: str,
		last_additionalfiles: List[str],
		additionalfiles: List[str],
		model: Any,
		signalStartLoading: pyqtSignal,
		signalStopLoading: pyqtSignal,
		signalProgressItem: pyqtSignal
	) -> None:
		"""
		Is called by the ChannelLoaderSaver thread when a save or saveas operation is issued by the user.

		:param filepath:
		:param encoding:
		:param last_additionalfiles:
		:param additionalfiles:
		:param model:
		:param signalStartLoading:
		:param signalStopLoading:
		:param signalProgressItem:
		:return:
		"""
		raise NotImplementedError

	@abstractmethod
	def readFile(
		self,
		filepath: str,
		encoding: str,
		last_additionalfiles: List[str],
		additionalfiles: List[str],
		model: Any,
		signalStartLoading: pyqtSignal,
		signalStopLoading: pyqtSignal,
		signalProgressItem: pyqtSignal
	) -> None:
		"""
		Is called by the ChannelLoaderSaver thread when an open operation is issued by the user.

		:param filepath:
		:param encoding:
		:param last_additionalfiles:
		:param additionalfiles:
		:param model:
		:param signalStartLoading:
		:param signalStopLoading:
		:param signalProgressItem:
		:return:
		"""
		raise NotImplementedError

	@abstractmethod
	def parseFileItem(self, channel: Channel, row: Any, extrajson: dict):
		"""
		Is called on every line when reading the input file, by Channel.__init()__

		:param channel:
		:param row:
		:param extrajson:
		:return:
		"""
		raise NotImplementedError

	def getPluginDict(self) -> dict:
		return self.plugindict

	def createTreeCategorys(self, model) -> List[Channel]:
		tc = self.getTreeCategories()
		plugindict = self.getPluginDict()
		channels = []
		for k, v in tc.items():
			cat = Channel(k, True, plugindict, model.channelfields, model.rootitem, True)
			for k1, v1 in v.items():
				cat.setDataByFieldName(k1, v1, True)
			channels.append(cat)
		return channels

	def createFields(self) -> dict:
		field_captions = self.getFieldCaptions()
		field_names = self.getFieldNames()
		visibility = self.getFieldVisibility()
		field_types = self.getFieldTypes()
		field_sortable = self.getFieldSortability()
		field_column_index = self.getFileColumnIndicies()

		fields = {}

		assert field_captions is not None, "field_captions invalid"
		assert field_names is not None, "field_names invalid"
		assert visibility is not None, "visibility invalid"
		assert field_types is not None, "field_types invalid"
		assert field_sortable is not None, "field_sortable invalid"
		assert field_column_index is not None, "field_column_index invalid"

		assert \
			len(field_captions) == len(field_names) == len(visibility) == len(field_types) == len(field_sortable), \
			"field information parameters lengths do not match"

		field_len = len(field_captions)

		for i in range(0, field_len):
			fields[field_names[i]] = ChannelField(
				i,
				field_captions[i],
				field_names[i],
				visibility[i],
				field_types[i],
				field_sortable[i],
				field_column_index[i]
			)

		return fields
