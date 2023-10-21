from typing import List, Dict, Any
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QAction, QMenu, QFileDialog
from model.ChannelField import ChannelFieldType
from tvplugins.ITVPlugin import ITVPlugin
from lib.Helpers import string_is_empty, count_file_rows, get_reformatted_exception
from model.Channel import Channel
from model.ChannelModel import ChannelModel
from lib.App import App
from collections import OrderedDict
from codecs import encode
from lib.Helpers import fill, is_empty_sequence, get_user_folder, UserFolderType


class TVPlugin(ITVPlugin):

	model = None
	""":type:ChannelModel"""

	app = None
	""":type:App"""

	def __init__(self, app):
		super(TVPlugin, self).__init__()
		self.app = app

	def getRegistryIndex(self):
		return 2

	def getFieldCaptions(self):
		return [
			"Kanal-Name", "Frequenz", "Satellit",
			"Service Type", "Line",
			"Preamble", "Addendum"
		]

	def getFieldNames(self):
		return [
			"name", "frequency", "satellite",
			"servicetype", "line",
			"preamble", "addendum"
		]

	def getFileColumnIndicies(self):
		return [
			0, 1, 2,
			-1, -1,
			-1, -1
		]

	def getFieldVisibility(self):
		return [
			True, True, True,
			False, False,
			False, False
		]

	def getFieldTypes(self):
		return [
			ChannelFieldType.String, ChannelFieldType.Integer, ChannelFieldType.String,
			ChannelFieldType.String, ChannelFieldType.String,
			ChannelFieldType.String, ChannelFieldType.String
		]

	def getFieldSortability(self) -> List[bool]:
		return [
			True, True, True,
			False, False,
			False, False
		]

	def getTreeCategories(self) -> OrderedDict:
		return OrderedDict([
			("TV", {"servicetype": "TV"}),
			("Radio", {"servicetype": "RADIO"}),
			("Unbekannt", {"servicetype": "UNKNOWN"}),
		])

	def addToTopLevelContextMenu(self, is_new_menu: bool, parentchannel: Channel, ctx: QMenu) -> None:
		if is_new_menu:
			qa = QAction("Kanallisten synchronisieren", ctx)
			qa.setData(["cs", parentchannel])
			ctx.insertAction(ctx.actions()[1], qa)
			ctx.insertSeparator(ctx.actions()[1])
			ctx.triggered.connect(self.onContextMenuOpened)

	def onContextMenuOpened(self, action: QAction):
		try:
			data = action.data()
			if self.model.allChannelCount() - 3 < 1:
				raise Exception("Es wurden Kanäle in die Hauptansicht geladen")

			if not is_empty_sequence(data) and data[0] == "cs":
				defaultfilepath = self.app.yamlGet("main", "lastchannel_filepath")
				if not string_is_empty(defaultfilepath):
					defaultfilepath = str(get_user_folder(UserFolderType.Desktop))
					filepath, filefilter = QFileDialog.getOpenFileName(
						self.app.mainwindow,
						"Kanalliste zum synchronisieren öffnen",
						defaultfilepath,
						self.app.channeltypefilter)

					if not string_is_empty(filepath):
						syncchannels = []
						""":type: List[Channel]"""

						with open(filepath, encoding=self.model.encoding, mode="rt") as f:
							for idx, row in enumerate(f):
								if not string_is_empty(row, False):
									syncchannels.append(Channel(row, False, self.plugindict, self.model.channelfields, None, None))

						if len(syncchannels) < 1:
							raise(Exception("Keine Kanäle in der Synchronisations-Liste gefunden"))

						self.model.layoutAboutToBeChanged.emit()

						tv = None
						radio = None
						unknown = None

						for c in self.model.rootitem.childchannels:
							st = c.getValueByFieldName("servicetype")
							if st == "TV":
								tv = c
							elif st == "RADIO":
								radio = c
							elif st == "UNKNOWN":
								unknown = c

						syncchannellen = len(syncchannels)

						insertedradio = 0
						insertedtv = 0
						insertedunknown = 0

						for i in range(syncchannellen-1, -1, -1):
							c = syncchannels[i]
							channelservicetype = c.getValueByFieldName("servicetype")

							parentchannel = None

							if channelservicetype == "RADIO":
								parentchannel = radio
								inserted = insertedradio
							elif channelservicetype == "TV":
								parentchannel = tv
								inserted = insertedtv
							elif channelservicetype == "UNKNOWN":
								parentchannel = unknown
								inserted = insertedunknown

							if parentchannel is not None:
								found = None
								""":type: Channel"""

								parentchannellen = len(parentchannel.childchannels)

								for j in range(inserted, parentchannellen-1):
									cs = parentchannel.childchannels[j]
									if cs.getValueByFieldName("name") == c.getValueByFieldName("name"):
										found = cs
										break

								if found is not None:
									parent = found.parentchannel
									""":type: Channel"""

									csindex = parent.childchannels.index(cs)
									parent.childchannels.pop(csindex)
									parent.childchannels.insert(0, cs)

									if channelservicetype == "RADIO":
										insertedradio += 1
									elif channelservicetype == "TV":
										insertedtv += 1
									elif channelservicetype == "UNKNOWN":
										insertedunknown += 1

						self.model.layoutChanged.emit()

		except Exception as e:
			self.model.showMessageboxException("ToshibaSBX.TVPlugin.onContextMenuOpened()", e)

	def parseFileItem(self, channel, row, extrajson):
		channel.values[channel.getFieldByName("line")] = row
		channel.values[channel.getFieldByName("servicetype")] = "RADIO" if row[28:29] == "R" else "TV"
		channel.values[channel.getFieldByName("frequency")] = row[69:75] + row[87:102]
		channel.values[channel.getFieldByName("satellite")] = row[10:28].lstrip().rstrip()
		channel.values[channel.getFieldByName("addendum")] = row[51:115]
		channel.values[channel.getFieldByName("preamble")] = row[0:43]
		name = row[43:51] + row[115:127].lstrip().rstrip()
		o1 = ord(name[0])
		o2 = ord(name[1])
		o3 = ord(name[2])
		if o1 == 5 or o1 == 21:
			name = name[1:]
		elif o1 == 16 and o2 == 0 and o3 == 7:
			name = name[3:]
		name = name.lstrip().rstrip()
		channel.values[channel.getFieldByName("name")] = name

	def writeFile(
		self,
		filepath: Any,
		encoding: str,
		last_additionalfiles: List[str],
		additionalfilesOld: List[str],
		model: Any,
		signalStartLoading: pyqtSignal,
		signalStopLoading: pyqtSignal,
		signalProgressItem: pyqtSignal
	):
		try:
			rootitemcount = model.rootitem.allChildCount()

			if rootitemcount <= 2:
				signalStartLoading.emit(0)
				signalStopLoading.emit([])
				return None

			signalStartLoading.emit(rootitemcount - 3)

			enc = 'windows-1252'

			count = 0

			with open(filepath, 'wb', -1) as f:
				for index, channel in enumerate(model.rootitem.childchannels):
					childchannels = channel.childchannels
					for it in childchannels:
						f.write(bytes(encode(
							it.values[channel.getFieldByName("preamble")],
							enc
						)))
						name = it.values[channel.getFieldByName("name")]
						f.write(bytes(encode(name[0:8], enc)))

						linelength = len(name)
						if linelength < 8:
							f.write(bytes(encode(fill(" ", 8 - linelength), enc)))
						f.write(bytes(encode(it.values[channel.getFieldByName("addendum")], enc)))
						postname = name[8:]
						f.write(bytes(encode(postname, enc)))
						linelength = len(postname)
						if linelength < 12:
							f.write(bytes(encode(fill(" ", 12 - linelength), enc)))
						f.write(bytes(encode(chr(10), enc)))
						signalProgressItem.emit((count,))
						count += 1
				f.write(b'\x00')
				for i in range(0, 127):
					f.write(bytes(' ', enc))
			signalStopLoading.emit([])

		except Exception as e:
			signalStopLoading.emit([
				"Fehler",
				"In ToshibaSBX.TVPlugin.writeFile()",
				None,
				get_reformatted_exception("", e)
			])

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
	):
		try:
			self.model = model
			plugindict = self.getPluginDict()
			treecats = self.createTreeCategorys(model)

			tv = treecats[0]
			radio = treecats[1]
			unknown = treecats[2]

			itemcount = count_file_rows(filepath, encoding)
			signalStartLoading.emit(itemcount + 3)
			signalProgressItem.emit((0, radio))
			signalProgressItem.emit((1, tv))
			signalProgressItem.emit((2, unknown))

			from struct import pack
			nulbyte = pack('B', 0)

			with open(filepath, encoding=encoding, mode="rt") as f:
				for idx, row in enumerate(f):
					if string_is_empty(row, False):
						continue
					firstbyte = row[0].encode(encoding)
					if firstbyte == nulbyte:
						continue
					c = Channel(row, False, plugindict, model.channelfields, None, None)
					channelservicetype = c.getValueByFieldName("servicetype")
					if channelservicetype == "RADIO":
						parentchannel = radio
					elif channelservicetype == "TV":
						parentchannel = tv
					else:
						parentchannel = unknown
					signalProgressItem.emit((idx + 3, parentchannel, c))

			signalStopLoading.emit([])

		except Exception as e:
			signalStopLoading.emit([
				"Fehler",
				"In ToshibaSBX.TVPlugin.readFile()",
				None,
				get_reformatted_exception("", e)
			])
