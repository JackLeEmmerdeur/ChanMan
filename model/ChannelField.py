from enum import Enum


class ChannelFieldType(Enum):
	String = 1
	Integer = 2
	Float = 3
	Boolean = 4


class ChannelField:

	columnindex = None
	""":type:int"""

	fieldcaption = None
	""":type: str"""

	fieldname = None
	""":type: str"""

	visible = None
	""":type: bool"""

	fieldtype = None
	""":type: SBXItemFieldType"""

	sortable = None
	""":type: bool"""

	filecolumnindex = None
	""":type: int"""

	def __init__(
		self,
		columnindex: int,
		fieldcaption: str,
		fieldname: str,
		visibility: bool,
		fieldtype: ChannelFieldType,
		sortable: bool,
		filecolumnindex: int
	):
		self.columnindex = columnindex
		self.fieldcaption = fieldcaption
		self.fieldname = fieldname
		self.visible = visibility
		self.fieldtype = fieldtype
		self.filecolumnindex = filecolumnindex
		self.sortable = sortable