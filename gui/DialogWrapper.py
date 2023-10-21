from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QKeyEvent, QCloseEvent
from PyQt5.QtWidgets import QDialog
# from PyQt5.QtCore import QThread


class DialogWrapper(QDialog):

	_ui = None
	_closingSignal = pyqtSignal(QCloseEvent)
	_keyPressSignal = pyqtSignal(QKeyEvent)

	def __init__(self, ui):
		super(DialogWrapper, self).__init__()
		self._ui = ui
		self._ui.setupUi(self)

	def ui(self):
		return self._ui
	#
	# def window(self):
	# 	return self._win
	#
	# def connectKeyPressEvent(self, func):
	# 	self._keyPressSignal.connect(func)
	#
	# def connectCloseEvent(self, func):
	# 	self._closingSignal.connect(func)
	#
	# def keyPressEvent(self, e):
	# 	self._keyPressSignal.emit(e)
	#
	# def closeEvent(self, e):
	# 	self._closingSignal.emit(e)
