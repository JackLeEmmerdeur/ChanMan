from typing import List, Dict
from tvplugins.ITVPlugin import ITVPlugin
from lib.Helpers import string_is_empty, is_sequence_with_any_elements
from pathlib import Path


class PluginsRegistry:
	mainPluginPath = None
	""":type: Path"""

	plugins = None
	""":type: list"""

	webview = None
	""":type: QWebEngineView"""

	def __init__(self):
		self.plugins = [
			{
				"name": "Group",
				"filefilter": "",
				"additionalfilefilter": None,
				"plugin": None
			},
			{
				"name": "SharpCVS",
				"models": ["LC-49CFE6242"],
				"filefilter": "SharpCSV(*.csv)",
				"additionalfilefilter": [
					"JSON(*.json)"
				],
				"plugin": None
			},
			{
				"name": "ToshibaSBX",
				"models": ["XOXO"],
				"filefilter": "ToshibaSDX(*.sdx)",
				"additionalfilefilter": None,
				"plugin": None
			},
			{
				"name": "PanasonicSQLite",
				"detectencoding": False,
				"models": ["LEL"],
				"filefilter": "PanasonicSQLite(*.db)",
				"additionalfilefilter": None,
				"plugin": None
			}
		]

	def setPluginPath(self, maindirpath: str):
		self.mainPluginPath = Path(maindirpath)
		self.mainPluginPath = self.mainPluginPath.joinpath("tvplugins")

	def getPluginPath(self):
		return self.mainPluginPath

	def getAssetsPath(self, rootpath: Path) -> Path:
		passets = rootpath.joinpath("assets")
		return passets

	def getFileFilters(self) -> str:
		return ";;".join(
			[
				keyvalue[1] for plugindict in self.plugins
					for keyvalue in plugindict.items()
						if keyvalue[0] == "filefilter" and not string_is_empty(keyvalue[1])
			]
		)

	def getPluginByFileFilter(self, filefilter: str) -> Dict[str, str]:
		p = None
		for plugin in self.plugins:
			if not string_is_empty(plugin["filefilter"]) and \
					plugin["filefilter"] == filefilter:
				p = plugin
				break
		return p

	def plugPlugins(self, plugins: List[ITVPlugin]) -> None:
		if self.plugins is not None and plugins is not None:
			for plugin in plugins:
				regindex = plugin.getRegistryIndex()
				if -1 < regindex < len(self.plugins):
					self.plugins[regindex]["plugin"] = plugin
					plugin.plugindict = self.plugins[regindex]

	def getPluginByIndex(self, index: int) -> str:
		if -1 < index < len(self.plugins):
			return self.plugins[index]
		return None

	def pluginsIter(self):
		if not is_sequence_with_any_elements(self.plugins):
			return None
		for i in self.plugins:
			yield i
