from typing import Callable

from PyQt5.QtCore import QThread, pyqtSignal

from lib.Helpers import string_is_empty, is_empty_sequence
from model.Channel import Channel
from model.ChannelField import ChannelField


class SearchThread(QThread):

	signalStart = pyqtSignal(int)
	""":type: pyqtSignal"""

	signalProgressItem = pyqtSignal(int, object)
	""":type: pyqtSignal"""

	signalStop = pyqtSignal()
	""":type: pyqtSignal"""

	rootitem = None
	""":type: Channel"""

	searchterm = None
	""":type: str"""

	caseSensitive = False
	""":type: bool"""

	searchSingleWords = True
	""":type: bool"""

	def __init__(
		self,
		rootitem: Channel,
		searchterm: str,
		caseSensitive: bool,
		searchSingleWords: bool,
		onSignalStartFunc: Callable,
		onSignalProgressFunc: Callable,
		onSignalStopFunc: Callable
	):
		QThread.__init__(self)
		self.rootitem = rootitem
		self.searchterm = searchterm

		self.caseSensitive = caseSensitive
		self.searchSingleWords = searchSingleWords

		self.signalStart.connect(onSignalStartFunc)
		self.signalStop.connect(onSignalStopFunc)
		self.signalProgressItem.connect(onSignalProgressFunc)

	def __del__(self):
		self.wait()

	def run(self):
		root_all_childcount = self.rootitem.allChildCount()

		self.signalStart.emit(root_all_childcount-3)

		channelindex = 0

		searchterm = self.searchterm.split() if self.searchSingleWords else self.searchterm
		searchmulti = string_is_empty(searchterm) and not is_empty_sequence(searchterm)

		if not self.caseSensitive:
			if searchmulti:
				searchterm[:] = [x.lower() for x in searchterm]
				for i in range(0, len(searchterm)):
					searchterm[i] = searchterm[i].lower()
			else:
				searchterm = searchterm.lower()

		for root_sub_channel in self.rootitem.childchannels:  # type: Channel
			for channel in root_sub_channel.childchannels:  # type: Channel
				found = None

				for field in channel.channelfields.iterateByIndex():  # type: ChannelField
					if field.visible:
						fieldval = str(channel.getValueByField(field))
						fieldval = fieldval if self.caseSensitive else fieldval.lower()
						if searchmulti:
							for searchtermatom in searchterm:
								if searchtermatom in fieldval:
									found = field
									break
						elif searchterm in fieldval:
							found = field

						if found:
							self.signalProgressItem.emit(channelindex, [channel, found])
							break

				if found is False:
					self.signalProgressItem.emit(channelindex, None)
				channelindex += 1

		self.signalStop.emit()
