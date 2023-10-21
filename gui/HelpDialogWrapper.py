from enum import Enum
from pathlib import Path
from typing import List, Tuple

from PyQt5.Qt import Qt
from PyQt5.QtCore import QModelIndex
from PyQt5.QtWidgets import QListWidgetItem, QTextBrowser
from ijson import parse as ijsonparse
from sortedcontainers import SortedDict

from gui.DialogWrapper import DialogWrapper
from gui.HelpDialog import Ui_HelpDialog
from lib.Helpers import is_integerish, string_is_empty, get_reformatted_exception
from lib.QTHelpers import remove_all_tabs, addLinebreakToTextDocument, addImageToTextDocument, \
	addHeaderToTextDocument, addTextToDocument, scrollTextBrowser
from tvplugins.PluginsRegistry import PluginsRegistry
from markdown import Markdown


class TopicItemType(Enum):
	Image = 1
	Paragraph = 2
	Header = 3
	Newline = 4

	def properties(self):
		if self.value == 1:
			return {
				"src": None,
				"caption": None,
				"captiontop": False,
				"maxwidth": None
			}
		elif self.value == 2:
			return {
				"text": None,
				"markdown": False
			}
		elif self.value == 3:
			return {
				"text": None
			}
		elif self.value == 4:
			return None


class HelpDialogWrapper:

	pluginregistry = None
	""":type: PluginsRegistry"""

	help_headerformats = {}
	""":type: Dict[int, QTextBlockFormat]"""

	pluginpath = None
	""":type: Path"""

	uihelpdialog = None
	""":type: Ui_HelpDialog"""

	helpdialog = None

	lastlink = None
	""":type: List[str]"""

	cached_tabs = None
	""":type: SortedDict"""  # {link:str: Tuple(sectionname:str, tab:QTextBrowser)}

	def __init__(self, maindirpath: str, pluginregistry: PluginsRegistry):

		self.cached_tabs = SortedDict()
		self.lastlink = None

		""":type: DialogWrapper"""
		self.uihelpdialog = Ui_HelpDialog()
		self.helpdialog = DialogWrapper(self.uihelpdialog)
		self.helpdialog.setModal(True)
		self.uihelpdialog.splitter.setSizes([100, 1000])
		self.pluginregistry = pluginregistry
		self.pluginpath = Path(maindirpath).joinpath("tvplugins")

		self.uihelpdialog.topicsList.selectionModel().currentRowChanged.connect(self.onListIndexChange)

		qi = QListWidgetItem("Hilfe")
		qi.setData(Qt.UserRole, 0)
		self.uihelpdialog.topicsList.addItem(qi)

		for pluginidx, i in enumerate(self.pluginregistry.pluginsIter()):
			if i["name"] == "Group":
				continue
			psub = self.pluginpath.joinpath(i["name"])
			if not psub.is_dir():
				continue
			jsonfile = psub.joinpath("help.json")
			if not jsonfile.is_file():
				continue
			qi = QListWidgetItem(i["name"])
			qi.setData(Qt.UserRole, pluginidx + 1)
			self.uihelpdialog.topicsList.addItem(qi)

	@staticmethod
	def linkToIndicies(link: str):
		if string_is_empty(link):
			return None
		return link.split(".")

	def onListIndexChange(self, current: QModelIndex, previous: QModelIndex):
		try:
			item2 = self.uihelpdialog.topicsList.itemFromIndex(previous)
			""":type:QListWidgetItem"""

			if item2 is None:
				return None

			item1 = self.uihelpdialog.topicsList.itemFromIndex(current)
			""":type:QListWidgetItem"""

			item1listindex = self.uihelpdialog.topicsList.row(item1)
			item2listindex = self.uihelpdialog.topicsList.row(item2)

			if item1listindex != item2listindex:
				self.setHelpListIndex("{}.0".format(item1listindex))

		except Exception as e:
			print(get_reformatted_exception("onListIndexChange", e))

	def lastLinkEquals(self, link: str, test_anchors: bool=False) -> Tuple[bool, bool, List[str]]:

		linklst = HelpDialogWrapper.linkToIndicies(link)
		lastlinklst = HelpDialogWrapper.linkToIndicies(self.lastlink)

		if linklst is None:
			return False, lastlinklst is None, None

		if lastlinklst is None:
			return False, False, None

		listindex_same = False

		if lastlinklst[0] == linklst[0]:
			listindex_same = True

		if len(lastlinklst) != len(linklst):
			return listindex_same, False, linklst
		else:
			equals = True
			for idx, ll in enumerate(linklst):
				if idx > 1 and test_anchors is False:
					break
				if lastlinklst[idx] != ll:
					equals = False
					break
			return listindex_same, equals, linklst

	def showWindow(self, link: str=None):
		self.setHelpListIndex(link)
		self.helpdialog.show()

	def setHelpListIndex(self, link: str):
		try:
			if self.lastlink is None:
				linklst = ["0", "0"]
			else:
				listindex_same, link_equals, linklst = self.lastLinkEquals(link)

				if link_equals:
					return None

				if listindex_same:
					self.uihelpdialog.topicSectionsTabs.setCurrentIndex(int(linklst[1]))
				elif linklst[0] + "." + linklst[1] in self.cached_tabs:
					remove_all_tabs(self.uihelpdialog.topicSectionsTabs)
					for k, v in self.cached_tabs.items():
						ll = HelpDialogWrapper.linkToIndicies(k)
						if ll[0] == linklst[0]:
							self.uihelpdialog.topicSectionsTabs.addTab(v[1], v[0])
					self.lastlink = link
					return None

			remove_all_tabs(self.uihelpdialog.topicSectionsTabs)

			listindex = int(linklst[0])

			self.uihelpdialog.topicsList.setCurrentRow(listindex)

			qi = self.uihelpdialog.topicsList.item(listindex)

			plugin_index = qi.data(Qt.UserRole)

			if plugin_index == 0:
				pluginpath = self.pluginpath
			else:
				plugin = self.pluginregistry.getPluginByIndex(plugin_index - 1)
				pluginpath = self.pluginpath.joinpath(plugin["name"])

			jsonfile = pluginpath.joinpath("help.json")

			topictitle = None

			textbrowser = QTextBrowser()
			""":type: QTextBrowser"""

			current_item = None

			standard_char_format = None
			""":type: QTextCharFormat"""

			markdown_proc = None
			""":type: Markdown"""

			topic_index = 0

			with open(str(jsonfile.absolute()), "rb") as f:
				for key, jsontype, value in ijsonparse(f):
					if key == "topics.item.title" and jsontype == "string":
						topictitle = value
						textbrowser = QTextBrowser()
						standard_char_format = textbrowser.currentCharFormat()

					if topictitle is not None:
						if key == "topics.item.items":
							if jsontype == "start_array":
								current_item = {}
							elif jsontype == "end_array":
								current_item = {}

						if current_item is not None and key == "topics.item.items.item.type":
							if value == "image":
								current_item["type"] = TopicItemType.Image
							elif value == "paragraph":
								current_item["type"] = TopicItemType.Paragraph
							elif value == "newline":
								current_item["type"] = TopicItemType.Newline
							elif value.find("header") > -1:
								shsize = value[6:]
								if not is_integerish(shsize):
									raise(Exception("header has to end with integer"))
								hsize = int(shsize)
								if hsize < 1 or hsize > 3:
									raise(Exception("header size has to be between 1 and 3"))
								current_item["type"] = TopicItemType.Header
								current_item["headersize"] = hsize
							else:
								raise(Exception("Topictype {} is invalid".format(value)))

							props = current_item["type"].properties()

							if props is not None:
								current_item = {**current_item, **props}

						if current_item is not None and key == "topics.item.items.item" and jsontype == "end_map":
							itemtype = current_item["type"]
							if itemtype == TopicItemType.Newline:
								addLinebreakToTextDocument(standard_char_format, textbrowser)
							elif itemtype == TopicItemType.Image:
								addImageToTextDocument(
									standard_char_format,
									textbrowser,
									pluginpath.joinpath(current_item["src"]).absolute(),
									current_item["caption"],
									current_item["captiontop"],
									current_item["maxwidth"]
								)
							elif itemtype == TopicItemType.Paragraph:
								if current_item["markdown"] is True and markdown_proc is None:
									markdown_proc = Markdown()

								addTextToDocument(
									standard_char_format,
									textbrowser,
									current_item["text"],
									current_item["markdown"],
									markdown_proc
								)
							elif itemtype == TopicItemType.Header:
								addHeaderToTextDocument(
									standard_char_format,
									textbrowser,
									current_item["headersize"],
									current_item["text"],
									self.help_headerformats
								)
							current_item.clear()

						if current_item is not None and "type" in current_item:
							itemtype = current_item["type"]
							if itemtype == TopicItemType.Image:
								if key == "topics.item.items.item.src":
									current_item["src"] = value
								elif key == "topics.item.items.item.caption":
									current_item["caption"] = value
								elif key == "topics.item.items.item.captiontop":
									current_item["caption"] = bool(value)
								elif key == "topics.item.items.item.maxwidth":
									current_item["maxwidth"] = None if not is_integerish(value) else int(value)
							elif itemtype == TopicItemType.Paragraph:
								if key == "topics.item.items.item.markdown":
									current_item["markdown"] = value
								elif key == "topics.item.items.item.text" and jsontype == "string":
									current_item["text"] = value
								elif key == "topics.item.items.item.text" and jsontype == "start_array":
									current_item["text"] = []
								elif key == "topics.item.items.item.text.item":
									current_item["text"].append(value)
							elif itemtype == TopicItemType.Header:
								if key == "topics.item.items.item.text":
									current_item["text"] = value

					if textbrowser is not None and key == "topics.item" and jsontype == "end_map":
						self.cached_tabs[str(listindex) + "."+str(topic_index)] = (topictitle, textbrowser)
						scrollTextBrowser(textbrowser, 0)
						self.uihelpdialog.topicSectionsTabs.addTab(textbrowser, topictitle)
						topic_index += 1

				self.uihelpdialog.topicSectionsTabs.setCurrentIndex(0)
				self.lastlink = str(listindex) + ".0"

		except Exception as e:
			print(get_reformatted_exception("setHelpListIndex", e))
