# from os import linesep
from typing import List, Dict, IO, Any
from lib.QTHelpers import messagebox_onetime
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMenu, QAction
import ijson.backends.yajl2 as ijson
from ijson import parse as ijsonparse
from sortedcontainers import SortedDict

from lib.Helpers import is_empty_sequence, is_empty_dict, string_is_empty, is_sequence, \
	is_integer, is_integerish, count_file_rows, strings_in_string_i, get_reformatted_exception, \
	detect_file_encoding, filepath_to_tmp, copy_file, delete_file
from model.Channel import Channel
from model.ChannelField import ChannelFieldType
from tvplugins.ITVPlugin import ITVPlugin
from collections import OrderedDict


class TVPlugin(ITVPlugin):

	VALID_JSON_VERSIONS = ["6308_dvb_v1.1"]

	filecomments = []
	app = None
	model = None

	json_version = None
	json_country = None

	def __init__(self, app):
		super(TVPlugin, self).__init__()
		self.app = app

	def getRegistryIndex(self) -> int:
		return 1

	def getFieldCaptions(self) -> List[str]:
		# Channel Name has to first always
		return [
			"Channel Name", "Channel Number", "Service Type",
			"HD", "Free/Scramble", "Frequency",
			"Polarity", "Symbol Rate"]

	def getFieldNames(self) -> List[str]:
		# Channel Name has to first always
		return [
			"name", "number", "servicetype",
			"hd", "free", "frequency",
			"polarity", "symbolrate"]

	def getFieldVisibility(self) -> List[bool]:
		return [
			True, True, True,
			True, True, True,
			True, True]

	def getFieldTypes(self) -> List[Any]:
		return [
			ChannelFieldType.String, ChannelFieldType.Integer, ChannelFieldType.String,
			ChannelFieldType.Boolean, ChannelFieldType.String, ChannelFieldType.Integer,
			ChannelFieldType.String, ChannelFieldType.Integer]

	def getFieldSortability(self) -> List[bool]:
		return [
			True, True, False,
			True, True, False,
			False, False
		]

	def getFileColumnIndicies(self) -> List[int]:
		return [
			1, 0, 2,
			-1, 3, 4,
			5, 6
		]

	def getTreeCategories(self) -> OrderedDict:
		return OrderedDict([
			("TV", {"servicetype": "DTV"}),
			("Radio", {"servicetype": "RADIO"}),
			("Data", {"servicetype": "DATA"})
		])

	def addToTopLevelContextMenu(self, is_new_menu: bool, parentchannel: Channel, ctx: QMenu) -> None:
		pass

	def reorderChannelNumbers(self, parentchannel: Channel):
		self.model.layoutAboutToBeChanged.emit()
		i = 1
		for childchannel in parentchannel.childchannels:  # type:Channel
			childchannel.setDataByFieldName("number", i)
			i += 1
		self.model.layoutChanged.emit()

	def csvfilerow(self, channel: Channel):
		row = ""
		for channelfield in channel.channelfields.iterateByIndex():
			if channelfield.visible and channelfield.filecolumnindex > -1:
				if len(row) > 0:
					row += ","
				row += str(channel.getValueByFieldName(channelfield.fieldname))
		return row

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
		save_location_same = False
		temp_mainfile = None
		temp_additionalfile = None
		try:
			rootitemcount = model.rootitem.allChildCount()

			if rootitemcount <= 3:
				signalStartLoading.emit(0)
				signalStopLoading.emit([])
				return None

			signalStartLoading.emit(rootitemcount - 3)
			count = 0
			selected_prog = None
			json_error_on = None

			if filepath == self.app.last_filename:
				save_location_same = True
				temp_mainfile = filepath_to_tmp(filepath)
				temp_additionalfile = filepath_to_tmp(additionalfiles[0])
			else:
				temp_mainfile = filepath
				temp_additionalfile = additionalfiles[0]

			with open(temp_mainfile, "wt", encoding=encoding) as csvoutfile:
				for filecomment in self.filecomments:
					csvoutfile.write(filecomment)
					csvoutfile.write("\n")

				lastjsonindex = 0

				with open(temp_additionalfile, "wt", encoding=encoding) as jsonoutfile:
					jsonoutfile.writelines([
						"{\n",
						'   "Country" : "{}",\n'.format(self.json_country),
						'   "DVBS_Ch_Table" : [\n',
					])

					for index, channel in enumerate(model.rootitem.childchannels):
						childchannels = channel.childchannels
						self.reorderChannelNumbers(channel)
						if is_empty_sequence(childchannels):
							continue

						if not is_empty_sequence(additionalfiles) and len(additionalfiles) == 1:
							restructured_json = self.json_restructure(
								signalStopLoading,
								jsonoutfile,
								last_additionalfiles[0],
								lastjsonindex,
								rootitemcount - 3,
								channel.getValueByFieldName("servicetype"),
								childchannels
							)
							if restructured_json is None:
								json_error_on = channel.getFieldByName("name")
								break
							elif selected_prog is None:
								selected_prog = restructured_json[0]
							lastjsonindex += len(restructured_json)

						for subchannel in childchannels:
							csvoutfile.write(self.csvfilerow(subchannel))
							csvoutfile.write("\n")
							signalProgressItem.emit((count,))
							count += 1

					csvoutfile.write("[E]\n")

					if json_error_on is not None:
						raise(Exception("Konnte JSON nicht für die Kategorie {} neu strukturieren".format(json_error_on)))

					self.json_write_additional_keys(model, jsonoutfile, self.app.last_additionalfiles[0], selected_prog)

			signalStopLoading.emit([])

		except Exception as e:
			signalStopLoading.emit([
				"Fehler",
				"In SharpCVS.TVPlugin.writeFile()",
				None,
				get_reformatted_exception("", e)
			])

		if save_location_same:
			copy_file(temp_mainfile, self.app.last_filename)
			copy_file(temp_additionalfile, self.app.last_additionalfiles[0])
			delete_file(temp_mainfile)
			delete_file(temp_additionalfile)

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
		try:
			self.model = model

			plugindict = self.getPluginDict()

			treecats = self.createTreeCategorys(model)

			tv = treecats[0]
			radio = treecats[1]
			data = treecats[2]

			resversion = TVPlugin.json_get_version_and_country(signalStopLoading, last_additionalfiles[0])

			if resversion is None:
				return None

			self.json_version, self.json_country = resversion

			if string_is_empty(self.json_version) or strings_in_string_i(self.json_version, TVPlugin.VALID_JSON_VERSIONS) == -1:
				signalStopLoading.emit([
					"Fehler",
					"In SharpCVS.TVPlugin.readFile",
					"Die Kanal-JSON-Version '{}' ist inkompatibel mit dieser Version".format(self.json_version)
				])
				return

			if not is_empty_sequence(last_additionalfiles) and len(last_additionalfiles) == 1:
				extrajson = TVPlugin.json_read(signalStopLoading, last_additionalfiles[0], {"video_type": "vt", "SatName": "sn"})

			if extrajson is None:
				signalStopLoading.emit([
					"Fehler",
					"In SharpCVS.TVPlugin.json_read",
					"Konnte keine weiteren Informationen aus der angegebenen JSON-Datei ermitteln"
				])
				return None

			itemcount = count_file_rows(filepath) - 2

			signalStartLoading.emit(itemcount+3)

			signalProgressItem.emit((0, radio))
			signalProgressItem.emit((1, tv))
			signalProgressItem.emit((2, data))

			with open(filepath, mode="rt", encoding=encoding) as f:
				import csv

				reader = csv.reader(f)

				for index, row in enumerate(reader):
					if index <= 2:
						if index == 0:
							if "DVBS Program Data!" not in row[0]:
								signalStopLoading.emit([
									"Fehler",
									"In SharpCVS.TVPlugin.readFile"
									"Die Kanal-CSV-Datei '{}' ist inkompatibel mit dieser Version".format(filepath)
								])
								return

						if index == 0 or index == 1:
							self.filecomments.append(row[0])
						else:
							self.filecomments.append(",".join(row))

					elif index > 2 and not is_empty_sequence(row) and len(row) == 7:
						channel = Channel(row, False, plugindict, model.channelfields, None, extrajson)
						channel.setTag("original_channel_number", int(channel.getValueByFieldName("number")))
						channelservicetype = channel.getValueByFieldName("servicetype")

						parentchannel = None

						if channelservicetype == "RADIO":
							parentchannel = radio
						elif channelservicetype == "DTV":
							parentchannel = tv
						elif channelservicetype == "DATA":
							parentchannel = data

						if parentchannel is not None:
							signalProgressItem.emit((index + 2, parentchannel, channel))

			signalStopLoading.emit([])

		except Exception as e:
			signalStopLoading.emit([
				"Fehler",
				"In SharpCVS.TVPlugin.readFile()",
				None,
				get_reformatted_exception("", e)
			])

	def parseFileItem(self, channel: Channel, row: Any, extrajson: dict):
		if is_sequence(row) and len(row) >= 7:
			isHD = False

			if extrajson is not None:
				if is_integerish(row[0]):
					channelindex = int(row[0])
					if channelindex in extrajson:
						jsonitem = extrajson[channelindex]

						# Video Type (1:SD, 2:HD)
						if "vt" in jsonitem and is_integerish(jsonitem["vt"]):
							isHD = int(jsonitem["vt"]) == 2

			channel.values[channel.getFieldByName("number")] = row[0]
			channel.values[channel.getFieldByName("name")] = row[1]
			channel.values[channel.getFieldByName("servicetype")] = row[2]
			channel.values[channel.getFieldByName("free")] = row[3]
			channel.values[channel.getFieldByName("frequency")] = row[4]
			channel.values[channel.getFieldByName("polarity")] = row[5]
			channel.values[channel.getFieldByName("symbolrate")] = int(row[6])
			channel.values[channel.getFieldByName("line")] = row
			channel.values[channel.getFieldByName("hd")] = isHD

	@staticmethod
	def json_write_additional_keys(model, jsonoutfile, jsoninputfilepath, selected_prog):
		started = False

		counttv = model.rootitem.childchannels[0].allChildCount()
		countradio = model.rootitem.childchannels[1].allChildCount()
		countdata = model.rootitem.childchannels[2].allChildCount()
		countall = counttv + countradio + countdata

		with open(jsoninputfilepath, "rt") as f:
			for l in f:

				if '"DefaultConfig"' in l:
					started = True

				if started:
					v = None
					if "current_prog_num" in l:
						v = "         \"01.current_prog_num\" : {},\n".format(selected_prog['02.prog_num'])
					elif "current_prog_num" in l:
						v = "         \"02.current_prog_type\" : \"{}\",\n".format(selected_prog['04.prog_type'])
					elif "current_prog_num" in l:
						v = "         \"03.current_dtv_route\" : \"DVBS\"\n"
					elif "prog_cnt" in l:
						v = "         \"02.prog_cnt\" : {},\n".format(countall)
					elif "dtv_cnt" in l:
						v = "         \"03.dtv_cnt\" : {},\n".format(counttv)
					elif "radio_cont" in l:
						v = "         \"04.radio_cont\" : {},\n".format(countradio)
					elif "data_cont" in l:
						v = "         \"05.data_cont\" : {}\n".format(countdata)

					if v is not None:
						jsonoutfile.write(v)
					else:
						jsonoutfile.write(l)

	@staticmethod
	def json_get_version_and_country(signalStopLoading: pyqtSignal, filepath: str):
		version = None
		country = None
		i = 0

		try:
			with open(filepath, "rb") as f:
				parser = ijsonparse(f)
				for prefix, event, value in parser:
					if not string_is_empty(prefix) and not string_is_empty(event):
						sprefix = prefix.lower()
						sevent = event.lower()
						if sevent == "string":
							if sprefix == "country":
								country = value
							elif sprefix == "version":
								version = value
					if not string_is_empty(version) and not string_is_empty(country):
						break
					i += 1
		except Exception as e:
			signalStopLoading.emit([
				"Fehler",
				"In SharpCVS.TVPlugin.json_get_version_and_country()",
				None,
				get_reformatted_exception("", e)
			])
			return None
		return version, country

	@staticmethod
	def json_is_valid_channelitem(event, prefix):
		return (event == "string" or event == "number") and prefix.startswith("DVBS_Ch_Table.item.")

	@staticmethod
	def json_restructure(
		signalStopLoading: pyqtSignal,
		jsonoutfile: IO,
		jsoninputfilepath: str,
		firstindex: int,
		total_items: int,
		parentchannel_type: str,
		channels: List[Channel],
	):
		try:
			if is_empty_sequence(channels):
				return None

			chanmap_current = {}
			""":type: Dict[int,Channel]"""

			restructured_json = SortedDict()
			""":type: SortedDict[SortedDict[str, Any]]"""

			channel = None
			""":type: Channel"""

			currentindex = firstindex

			for c in channels:
				chanmap_current[c.getTag("original_channel_number")] = c  #

			with open(jsoninputfilepath, mode="rb") as f:
				parser = ijsonparse(f)
				current_json_channel = None

				for idx, (prefix, event, value) in enumerate(parser):
					if TVPlugin.json_is_valid_channelitem(event, prefix):

						keys = prefix.split(".")
						keytype = keys[3]

						if keytype == "index":
							channel = None
							prog_type = None
						if keytype == "prog_num":
							prog_num = value
						elif keytype == "prog_type":
							prog_type = value
							if prog_type == parentchannel_type:
								channel = chanmap_current.get(prog_num)
								current_json_channel = SortedDict()
								if channel is not None:
									channelindex = channels.index(channel)

									current_json_channel["01.index"] = channelindex + firstindex
									current_json_channel["02.prog_num"] = int(channel.getValueByFieldName("number"))
									current_json_channel["03.prog_name"] = channel.getValueByFieldName("name")
									current_json_channel["04.prog_type"] = prog_type
									restructured_json[channelindex] = current_json_channel
									currentindex += 1

						elif channel is not None and prog_type is not None and prog_type == parentchannel_type:
							current_json_channel[keys[2] + "." + keys[3]] = value

							if keytype == "Single Cable LNB Index":
								if currentindex == total_items:
									break

				for channelindex, restructured_json_item in restructured_json.items():
					jsonoutfile.write("      {")
					jsonoutfile.write("\n")
					for itemidx, (k, v) in enumerate(restructured_json_item.items()):
						jsonoutfile.write('         "{}" : {}'.format(
							k,
							str(v) if is_integer(v) else '"{}"'.format(v)
						))
						if itemidx < 50:
							jsonoutfile.write(",")
							jsonoutfile.write("\n")
					jsonoutfile.write("\n")
					jsonoutfile.write("      }")

					if (channelindex + firstindex) < total_items - 1:
						jsonoutfile.write(",")
						jsonoutfile.write("\n")
					else:
						jsonoutfile.write("\n")
						jsonoutfile.write("   ],")
						jsonoutfile.write("\n")

			return restructured_json
		except Exception as e:
			signalStopLoading.emit([
				"Fehler",
				"In SharpCVS.TVPlugin.json_restructure()",
				None,
				get_reformatted_exception("", e)
			])
			return None

	@staticmethod
	def json_read(signalStopLoading: pyqtSignal, filepath: str, channelitemkeys: dict):
		try:
			if is_empty_dict(channelitemkeys):
				return None

			if string_is_empty(filepath):
				return None

			with open(filepath, "rb") as f:

				parser = ijsonparse(f)
				lastprognum = None
				channelitems = None
				channeldict = {}
				i = 0

				for (prefix, event, value) in parser:
					if TVPlugin.json_is_valid_channelitem(event, prefix):
						if prefix.endswith(".prog_num"):
							if lastprognum is not None and channelitems is not None:
								channeldict[lastprognum] = channelitems
								i += 1
							channelitems = {}
							lastprognum = value

						for k, v in channelitemkeys.items():
							if prefix.endswith("." + k):
								channelitems[v] = value

				return channeldict
			return None

		except Exception as e:
			signalStopLoading.emit([
				"Fehler",
				"In SharpCVS.TVPlugin.json_read()",
				None,
				get_reformatted_exception("", e)
			])
			return None
