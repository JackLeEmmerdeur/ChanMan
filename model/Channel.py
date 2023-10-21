from typing import Any, List

from lib.Helpers import is_empty_sequence
from lib.Helpers import string_is_empty
from model.ChannelField import ChannelField
from model.ChannelFieldList import ChannelFieldList


class Channel(object):

	channelfields = None
	""":type: ChannelFieldList"""

	values = None
	""":type: dict[ChannelField, any]"""

	parentchannel = None
	""":type: Channel"""

	pluginmodule = None
	""":type: Any"""

	# If true, then this channel contains only childs and no column-values
	isgroup = False
	""":type: bool"""

	childchannels = None
	""":type: List[Channel]"""

	tags = None
	""":type: Dict[str, Any]"""

	def __init__(
		self,
		row: Any = None,
		is_group: bool = False,
		pluginmodule: Any = None,
		channelfieldlist: ChannelFieldList = None,
		parentchannel: Any = None,
		extrajson: dict = None
	):
		"""

		:param Any row: Either a line from an exported tv-channellist-file OR a CSV-fileline preparsed into a sequence OR the
		name of group in case channeltype is ChannelType.Group
		:param bool is_group:
		:param dict pluginmodule:
		:param ChannelFieldList channelfieldlist:
		:param Channel parentchannel:
		:param obj extrajson:
		"""
		self.channelfields = channelfieldlist
		self.pluginmodule = pluginmodule
		self.values = {}
		self.childchannels = []
		self.parentchannel = parentchannel

		if is_group is True or pluginmodule is None or pluginmodule["name"] == "Group":
			self.values[self.getFieldByName("number")] = -1
			self.values[self.getFieldByName("name")] = row
			self.isgroup = True
		else:
			pluginmodule["plugin"].parseFileItem(self, row, extrajson)

	def clear(self):
		self.values.clear()
		self.parentchannel = None
		self.pluginmodule = None

		if self.childchannels is not None:
			for cc in self.childchannels:  # type: Channel
				cc.clear()

		if self.tags is not None:
			self.tags.clear()

	def getFieldByName(self, channelfield_name: str) -> ChannelField:
		return self.channelfields.getFieldByName(channelfield_name)

	def getFieldByColumnIndex(self, columnindex: int):
		return self.channelfields.getFieldByColumnIndex(columnindex)

	def getValueByFieldName(self, channelfield_name: str) -> Any:
		if not string_is_empty(channelfield_name):
			channelfield = self.channelfields.getFieldByName(channelfield_name)
			if channelfield is not None:
				return self.values.get(channelfield)
		return None

	def getValueByField(self, channelfield: ChannelField) -> Any:
		if channelfield is not None and \
			not is_empty_sequence(self.values) and \
			channelfield in self.values:
			return self.values[channelfield]

	def setTag(self, name: str, obj: Any):
		if self.tags is None:
			self.tags = {}
		self.tags[name] = obj

	def getTag(self, name: str):
		if self.tags is None:
			return None
		return self.tags.get(name)

	def insertChild(self, newchildchannel, index):
		self.childchannels.insert(index, newchildchannel)

	def appendChild(self, newchildchannel):
		"""
		:type newchildchannel: Channel
		:param newchildchannel: A child Channel to this item
		:return:
		"""
		self.childchannels.append(newchildchannel)

	def removeChildByIndex(self, index):
		return self.childchannels.pop(index)

	def removeChildByChannel(self, channel):
		self.childchannels.remove(channel)

	def allChildCount(self):
		if is_empty_sequence(self.childchannels):
			return 0
		childcount = 0
		for childchannel in self.childchannels:
			childcount += childchannel.allChildCount()
		return childcount + len(self.childchannels)

	def childCount(self):
		return len(self.childchannels)

	def columnCount(self):
		return self.channelfields.countVisible()

	def setDataByField(self, field: ChannelField, value: Any, force=False) -> bool:
		"""

		:param field: The field you want to set the internal value to
		:param value: The value to to set to the field
		:param force: If `field` is not present in internal values it's created
		if `force` is True. If it's False no value is set.
		:return: True if value was set
		"""
		if field is not None:
			field_is_present = field in self.values
			if (not field_is_present and force) or field_is_present:
				self.values[field] = value
				return True
		return False

	def setDataByFieldName(self, name: str, value: Any, force=False) -> bool:
		return self.setDataByField(self.getFieldByName(name), value, force)

	def setDataByColumnIndex(self, columnindex: int, value: Any, force=False) -> bool:
		return self.setDataByField(self.getFieldByColumnIndex(columnindex), value, force)

	def setDataByColumnIndex(self, columnindex: int, value: Any, force=False) -> bool:
		return self.setDataByField(self.getFieldByColumnIndex(columnindex), value, force)

	def child(self, index):
		return self.childchannels[index]

	def data(self, columnindex):
		channelfield = self.getFieldByColumnIndex(columnindex)
		if self.isgroup:
			if channelfield.fieldname == "name":
				return self.values[channelfield]
		else:
			if channelfield is not None and channelfield in self.values:
				return self.values[channelfield]
		return None

	def row(self):
		if self.parentchannel:
			return self.parentchannel.childchannels.index(self)
		return 0

	def parentItem(self):
		return self.parentchannel

	def setParent(self, parentchannel):
		self.parentchannel = parentchannel

	def getParent(self):
		return self.parentchannel

	def __len__(self):
		return len(self.childchannels)

	def __str__(self):
		return self.values[self.getFieldByName("name")]
