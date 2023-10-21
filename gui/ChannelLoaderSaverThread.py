from PyQt5.QtCore import QThread, pyqtSignal


class ChannelLoaderSaver(QThread):
	callbackmethod = None
	filepath = None
	last_additionalfiles = None
	additionalfiles = None
	pluginmodule = None
	model = None
	signalBeforeInit = pyqtSignal()
	signalAfterInit = pyqtSignal()
	signalStart = pyqtSignal(int)  # 1st Argument: Total number of channels in file
	signalProgressItem = pyqtSignal(tuple) # variable args: 0[int]=progressvalue, 1[Channel/optional]=rootchannelitem, 2[Channel/optional]=subchannelitem
	signalStop = pyqtSignal(list)

	def __init__(self, model, filepath, last_additionalfiles, additionalfiles, pluginmodule, plugincallbackmethod):
		QThread.__init__(self)
		self.model = model
		self.callbackmethod = plugincallbackmethod
		self.filepath = filepath
		self.last_additionalfiles = last_additionalfiles
		self.additionalfiles = additionalfiles
		self.pluginmodule = pluginmodule

	def __del__(self):
		self.wait()

	def run(self):
		self.signalBeforeInit.emit()
		self.callbackmethod(
			self.filepath,
			self.model.encoding,
			self.last_additionalfiles,
			self.additionalfiles,
			self.model,
			self.signalStart,
			self.signalStop,
			self.signalProgressItem
		)
		self.signalAfterInit.emit()
