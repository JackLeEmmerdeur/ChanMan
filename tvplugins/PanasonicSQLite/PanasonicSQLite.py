# from os import linesep
from typing import List, Dict, IO, Any

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMenu, QAction
from ijson import parse as ijsonparse
from sortedcontainers import SortedDict

from lib.Helpers import is_empty_sequence, is_empty_dict, string_is_empty, is_sequence, \
	is_integer, is_integerish, count_file_rows, strings_in_string_i
from model.Channel import Channel
from model.ChannelField import ChannelFieldType
#from tvplugins.ITVPlugin import ITVPlugin
from tvplugins.ITVPlugin import ITVPlugin
from plumbum import local, FG, ProcessExecutionError
from pathlib import Path
from collections import OrderedDict


class TVPlugin(ITVPlugin):

	app = None
	model = None

	def __init__(self, app):
		super(TVPlugin, self).__init__()
		self.app = app

	def getRegistryIndex(self) -> int:
		return 3

	def getFieldCaptions(self) -> List[str]:
		# Channel Name has to first always
		return [
			"Channel Name", "Channel Number", "SQL-Table"
		]

	def getFieldNames(self) -> List[str]:
		# Channel Name has to first always
		return [
			"name", "number", "sqltable"
		]

	def getFieldVisibility(self) -> List[bool]:
		return [
			True, True, True
		]

	def getFieldTypes(self) -> List[Any]:
		return [
			ChannelFieldType.String, ChannelFieldType.Integer, ChannelFieldType.String
		]

	def getFileColumnIndicies(self) -> List[int]:
		return [
			1, 0, 2
		]

	def getFieldSortability(self) -> List[bool]:
		return [
			True, True, True
		]

	def getTreeCategories(self) -> OrderedDict:
		return OrderedDict([
			("TV", {"servicetype": "DTV"}),
			("Radio", {"servicetype": "RADIO"}),
			("Data", {"servicetype": "DATA"})
		])

	def addToTopLevelContextMenu(self, is_new_menu: bool, parentchannel: Channel, ctx: QMenu) -> None:
		pass

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
		pass
		# rootitemcount = model.rootitem.allChildCount()
		#
		# if rootitemcount <= 3:
		# 	signalStartLoading.emit(0)
		# 	signalStopLoading.emit([])
		# 	return None
		#
		# signalStartLoading.emit(rootitemcount-3)
		# count = 0
		# print(filepath)
		# print(additionalfiles)
		# #
		# # with open("/home/buccaneersdan/Schreibtisch/test.csv", "wt") as csvoutfile:
		# # 	for filecomment in self.filecomments:
		# # 		csvoutfile.write(filecomment)
		# # 		csvoutfile.write(linesep)
		# #
		# # 	lastjsonindex = 0
		# #
		# # 	with open("/home/buccaneersdan/Schreibtisch/test.json", "wt") as jsonoutfile:
		# # 		jsonoutfile.writelines([
		# # 				"{",
		# # 				linesep,
		# # 				'   "Country" : "{}",'.format(self.json_country),
		# # 				linesep,
		# # 				'   "DVBS_Ch_Table" : [',
		# # 				linesep
		# # 			]
		# # 		)
		# #
		# # 		for index, channel in enumerate(model.rootitem.childchannels):
		# # 			childchannels = channel.childchannels
		# #
		# # 			if is_empty_sequence(childchannels):
		# # 				continue
		# #
		# # 			if not is_empty_sequence(additionalfiles) and len(additionalfiles) == 1:
		# # 				restructured_json = self.json_restructure(
		# # 					jsonoutfile,
		# # 					additionalfiles[0],
		# # 					lastjsonindex,
		# # 					rootitemcount - 3,
		# # 					channel.getValueByFieldName("servicetype"),
		# # 					childchannels
		# # 				)
		# # 				lastjsonindex += len(restructured_json)
		# #
		# # 			for subchannel in childchannels:
		# # 				csvoutfile.write(self.csvfilerow(subchannel))
		# # 				csvoutfile.write(linesep)
		# # 				signalProgressItem.emit(count)
		# # 				count += 1
		# #
		# # 		self.json_write_additional_keys(jsonoutfile, additionalfiles[0])
		# # 		jsonoutfile.write(linesep)
		#
		# signalStopLoading.emit([])

	def readFile(
			self,
			filepath: str,
			encoding: str,
			additionalfiles: List[str],
			model: Any,
			signalStartLoading: pyqtSignal,
			signalStopLoading: pyqtSignal,
			signalProgressItem: pyqtSignal

	) -> None:

		try:
			p = Path(filepath)
			if p.is_file():
				has_tmp = False
				testp = None
				i = 0
				while not has_tmp:
					testp = Path(p.parent)
					testp = testp.joinpath("{}_tmp_{}{}".format(p.stem, i, p.suffix))

					if not testp.exists():
						has_tmp = True
					i += 1
					if i == 5:
						break

				if not has_tmp:
					raise(Exception("XOXO--\|/--SUXXOR~~!1!!"))
				else:

					decrypt = local["./tvplugins/PanasonicSQLite/DecryptSQLite"]

					decrypt.run([filepath, "/home/buccaneersdan/Schreibtisch/test.db"]) #testp.absolute()

					# testp.unlink()

		except ProcessExecutionError as e:
			print("Error {}: {}".format(e.retcode if e.retcode else e.errno, e.stderr))
		except Exception as e2:
			print(e2)

		# self.model = model
		#
		# radio = Channel("Radio", True, pluginmodule, model.channelfields, model.rootitem, True)
		# radio.setDataByFieldName("servicetype", "RADIO", True)
		#
		# tv = Channel("TV", True, pluginmodule, model.channelfields, model.rootitem, True)
		# tv.setDataByFieldName("servicetype", "DTV", True)
		#
		# data = Channel("Data", True, pluginmodule, model.channelfields, model.rootitem, True)
		# data.setDataByFieldName("servicetype", "DATA", True)
		#
		# self.json_version, self.json_country = TVPlugin.json_get_version_and_country(additionalfiles[0])
		#
		# if string_is_empty(self.json_version) or not strings_in_string_i(self.json_version, TVPlugin.VALID_JSON_VERSIONS):
		# 	signalStopLoading.emit([
		# 		"Fehler in SharpCVS.TVPlugin.readFile",
		# 		"Die Kanal-JSON-Version '{}' ist inkompatibel mit dieser Version".format(self.json_version)
		# 	])
		# 	return
		#
		# if not is_empty_sequence(additionalfiles) and len(additionalfiles) == 1:
		# 	extrajson = TVPlugin.json_read(additionalfiles[0], {"video_type": "vt", "SatName": "sn"})
		#
		# itemcount = count_file_rows(filepath) - 2
		#
		signalStartLoading.emit(0)
		#
		# with open(filepath, mode="rt", encoding=encoding) as f:
		# 	import csv
		#
		# 	reader = csv.reader(f)
		#
		# 	for index, row in enumerate(reader):
		# 		if index <= 2:
		# 			if index == 0:
		# 				if "DVBS Program Data!" not in row[0]:
		# 					signalStopLoading.emit([
		# 						"Fehler in SharpCVS.TVPlugin.readFile",
		# 						"Die Kanal-CSV-Datei '{}' ist inkompatibel mit dieser Version".format(filepath)
		# 					])
		# 					return
		#
		# 			if index == 0 or index == 1:
		# 				self.filecomments.append(row[0])
		# 			else:
		# 				self.filecomments.append(",".join(row))
		#
		# 		elif index > 2 and not is_empty_sequence(row) and len(row) == 7:
		# 			channel = Channel(row, False, pluginmodule, model.channelfields, None, extrajson)
		# 			channel.setTag("original_channel_number", int(channel.getValueByFieldName("number")))
		# 			channelservicetype = channel.getValueByFieldName("servicetype")
		#
		# 			if channelservicetype == "RADIO":
		# 				parentchannel = radio
		# 			elif channelservicetype == "DTV":
		# 				parentchannel = tv
		# 			elif channelservicetype == "DATA":
		# 				parentchannel = data
		#
		# 			channel.setParent(parentchannel)
		# 			parentchannel.appendChild(channel)
		# 			signalProgressItem.emit(index - 2)
		#
		# 	model.rootitem.appendChild(radio)
		# 	model.rootitem.appendChild(tv)
		# 	model.rootitem.appendChild(data)
		#
		signalStopLoading.emit([])

	def parseFileItem(self, channel: Channel, row: Any, extrajson: dict):
		pass
		# if is_sequence(row) and len(row) >= 7:
		# 	isHD = False
		#
		# 	if extrajson is not None:
		# 		if is_integerish(row[0]):
		# 			channelindex = int(row[0])
		# 			if channelindex in extrajson:
		# 				jsonitem = extrajson[channelindex]
		#
		# 				# Video Type (1:SD, 2:HD)
		# 				if "vt" in jsonitem and is_integerish(jsonitem["vt"]):
		# 					isHD = int(jsonitem["vt"]) == 2
		#
		# 	channel.values[channel.getFieldByName("number")] = row[0]
		# 	channel.values[channel.getFieldByName("name")] = row[1]
		# 	channel.values[channel.getFieldByName("servicetype")] = row[2]
		# 	channel.values[channel.getFieldByName("free")] = True if row[3] == "Free" else False
		# 	channel.values[channel.getFieldByName("frequency")] = row[4]
		# 	channel.values[channel.getFieldByName("polarity")] = row[5]
		# 	channel.values[channel.getFieldByName("symbolrate")] = int(row[6])
		# 	channel.values[channel.getFieldByName("line")] = row
		# 	channel.values[channel.getFieldByName("hd")] = isHD
