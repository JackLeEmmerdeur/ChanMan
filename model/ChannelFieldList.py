from model.ChannelField import ChannelField


class ChannelFieldList:
	cached_sorted_channelfields = None
	""":type: list"""

	fields = None
	""":type: dict[str, ChannelField]"""

	def __init__(self):
		self.fields = {}

	# def add(self, fieldcaption: str, fieldname: str, visibility: bool, fieldtype: ChannelFieldType, filecolumnindex: int) -> ChannelField:
	# 	f = ChannelField(len(self.fields), fieldcaption, fieldname, visibility, fieldtype, filecolumnindex)
	# 	self.fields[fieldname] = f
	# 	return f

	def clear(self):
		if self.fields is not None:
			self.fields.clear()

	def reInitFromChannelType(self, pluginmodule):
		if self.fields is not None:
			self.fields.clear()
		self.fields = pluginmodule["plugin"].createFields()

	def getFieldByName(self, fieldname: str) -> ChannelField:
		if self.fields is not None:
			f = self.fields.get(fieldname)
			return f
		return None

	def getFieldByColumnIndex(self, columnindex: int) -> ChannelField:
		channelfield = None
		if self.fields is not None:
			for k, v in self.fields.items():
				if v is not None:
					if v.columnindex == columnindex:
						channelfield = v
						break
		return channelfield

	def countAll(self):
		if self.fields is not None:
			return len(self.fields)
		return 0

	def countVisible(self):
		c = 0
		if self.fields is not None:
			for k, v in self.fields.items():
				if v.visible is True:
					c += 1
		return c

	def iterateByIndex(self):
		if self.cached_sorted_channelfields is None:
			self.cached_sorted_channelfields = sorted(self.fields.items(), key=lambda kv: kv[1].filecolumnindex)

			l = len(self.cached_sorted_channelfields)

			i = l - 1

			while i > -1:
				if self.cached_sorted_channelfields[i][1].filecolumnindex == -1:
					self.cached_sorted_channelfields.append(self.cached_sorted_channelfields[i])
					self.cached_sorted_channelfields.pop(i)
				i -= 1

		for csc in self.cached_sorted_channelfields:
			yield csc[1]

	@staticmethod
	def createChannelFieldListByChannelType(pluginmodule):
		cf = ChannelFieldList()
		cf.fields = pluginmodule["plugin"].createFields()
		return cf
