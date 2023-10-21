from PyQt5.QtWidgets import QMessageBox, QSpacerItem, QSizePolicy, QWidget
from lib.Helpers import is_integer, string_is_empty
from PyQt5.Qt import QUrl, QColor, QModelIndex
from PyQt5.QtWidgets import QApplication, QStyleFactory, QTabWidget, QTextBrowser, QListWidget, QListWidgetItem
from PyQt5.QtGui import QKeyEvent, QCloseEvent, QPixmap, QTextDocument, QTextCursor, \
	QImage, QImageReader, QTextImageFormat, QTextBlockFormat, QTextCharFormat, QFont, QTextFrameFormat, QBrush
from pathlib import Path
from typing import Union, Dict
from markdown import Markdown


def removeListWidgetItemByIndex(listwidget: QListWidget, index: QModelIndex):
	if listwidget is not None and index is not None and index.isValid():
		item = listwidget.itemFromIndex(index)
		""":type: QListWidgetItem"""
		i = listwidget.row(item)
		listwidget.takeItem(i)
		# listwidget.rowsAboutToBeRemoved(index.parent(), i,  i)
		# listwidget.removeItemWidget(item)
		# del item


def scrollTextBrowser(b: QTextBrowser, position: int):
	c = b.textCursor()
	c.setPosition(0)
	b.setTextCursor(c)


def addTextToDocument(
		standard_char_format: QTextCharFormat,
		b: QTextBrowser,
		text: str,
		markdown: bool=False,
		markdownproc: Markdown=None
):
	cursor = b.textCursor()
	""":type:QTextCursor"""

	cursor.insertBlock()

	if markdown:
		txt = "<br>".join(text)
		md = markdownproc.reset().convert(txt)
		cursor.insertHtml(md)
	else:
		txt = "\n".join(text)
		cursor.insertText(txt, standard_char_format)


def addHeaderToTextDocument(
	standard_char_format: QTextCharFormat,
	b: QTextBrowser,
	headersize: int,
	text: str,
	headerformats: Dict[int, QTextCharFormat]
):
	cursor = b.textCursor()
	""":type:QTextCursor"""

	if headersize not in headerformats:
		fmt = QTextCharFormat(standard_char_format)
		if headersize == 1:
			fmt.setFontPointSize(20)
		elif headersize == 2:
			fmt.setFontPointSize(15)
		elif headersize == 3:
			fmt.setFontPointSize(10)
		fmt.setFontWeight(QFont.Bold)
		fmt.setFontUnderline(True)
		headerformats[headersize] = fmt
	else:
		fmt = headerformats[headersize]

	cursor.insertBlock()

	cursor.insertText(text + "\n", fmt)


def addLinebreakToTextDocument(
	standard_char_format: QTextCharFormat,
	b: QTextBrowser
):
	cursor = b.textCursor()
	""":type:QTextCursor"""

	cursor.insertBlock()
	cursor.insertText("\n", standard_char_format)


def addImageToTextDocument(
	standard_char_format: QTextCharFormat,
	b: QTextBrowser,
	path: Path,
	caption: str=None,
	caption_placement_top: bool=False,
	maxwidth: int=None
):
	doc = b.document()
	""":type: QTextDocument"""

	cursor = b.textCursor()
	""":type:QTextCursor"""

	strpath = str(path.absolute())

	uri = QUrl("file://" + strpath)

	img = QImageReader(strpath).read()
	""":type:QImage"""

	doc.addResource(QTextDocument.ImageResource, uri, img)
	imgformat = QTextImageFormat()
	w = img.width()
	h = img.height()
	if maxwidth is not None:
		if w > maxwidth:
			d = float(maxwidth) / w
			w = maxwidth
			h = h * d
	imgformat.setWidth(w)
	imgformat.setHeight(h)
	imgformat.setName(strpath)

	has_caption = not string_is_empty(caption)

	if has_caption and caption_placement_top:
		cursor.insertBlock()
		cursor.insertText(caption, standard_char_format)

	cursor.insertBlock()
	cursor.insertImage(imgformat)

	if has_caption and not caption_placement_top:
		cursor.insertBlock()
		cursor.insertText(caption + "\n", standard_char_format)

	print("Doc all formats:{}".format(len(doc.allFormats())))


def remove_all_tabs(tabwidget: QTabWidget, delete_tabwidget=False):
	if tabwidget is not None:
		c = tabwidget.count()
		i = c - 1
		while i >= 0:
			if delete_tabwidget:
				w = tabwidget.widget(i)
				w.close()
				w.deleteLater()
				del w
			tabwidget.removeTab(i)
			i -= 1


def getStyles():
	return ",".join(QStyleFactory.keys())


def setStyle(qapp: QApplication, stylename: str):
	if stylename in QStyleFactory.keys():
		qapp.setStyle(stylename)
	else:
		messagebox_onetime("Qt Style error", "Qt Style {} could not be set".format(stylename))


def question(
	parent_window: QWidget,
	title: str,
	questionstr: str,
	default_button_yes_or_no: bool
) -> bool:
	buttons = QMessageBox.Yes | QMessageBox.No

	r = QMessageBox.question(
		parent_window,
		title,
		questionstr,
		buttons,
		QMessageBox.Yes if default_button_yes_or_no else QMessageBox.No
	)
	return r == QMessageBox.Yes


def messagebox_onetime(
	window_title: str,
	short_text: str,
	informative_text: str=None,
	detailed_text: str=None,
	width: int=None,
	height: int=None,
) -> QMessageBox:
	"""
	Shows a messagebox but creates a new messagebox on every function call

	:param window_title: Doh!
	:param short_text: A short introduction text
	:param informative_text: A descriptive text under the short introduction
	:param detailed_text: A detailed text in a messagebox, which is not shown if None
	:param width: Additional width. If None the messagebox is scaled appropriately
	:param height: Additional height. If None the messagebox is scaled appropriately
	:return: None
	"""
	return messagebox(None, window_title, short_text, informative_text, width, height, detailed_text)


def messagebox(
		previous_messagebox: QMessageBox,
		window_title: str,
		short_text: str,
		informative_text: str=None,
		detailed_text: str = None,
		show_cancel: bool=False,
		width: int=None,
		height: int=None
) -> QMessageBox:
	"""
	Shows a messagebox but lets you reuse a previous messagebox for fun and profit

	:param previous_messagebox: A previously used messagebox. Boosts performance. Maybe. Can be None.
	:param window_title: Doh!
	:param short_text: A short introduction text
	:param informative_text: A descriptive text under the short introduction
	:param detailed_text: A detailed text in a messagebox, which is not shown if None
	:param show_cancel: Show a cancel button
	:param width: Additional width. If None the messagebox is scaled appropriately.
	:param height: Additional height. If None the messagebox is scaled appropriately.
	:return: The previous_messagebox or a new messagebox if parameter was None
	"""
	if previous_messagebox is not None:
		infobox = previous_messagebox
	else:
		infobox = QMessageBox()

	infobox.setText(short_text)
	infobox.setInformativeText(informative_text)
	infobox.setWindowTitle(window_title)
	if detailed_text is not None:
		infobox.setDetailedText(detailed_text)
		width = 500
	buttons = QMessageBox.Ok
	if show_cancel:
		buttons |= QMessageBox.Cancel
	infobox.setStandardButtons(buttons)
	infobox.setEscapeButton(QMessageBox.Close)

	layout = None

	if is_integer(width):
		qs = QSpacerItem(width, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
		layout = infobox.layout()
		layout.addItem(qs, layout.rowCount(), 0, 1, layout.columnCount())

	if is_integer(height):
		qs = QSpacerItem(0, height, QSizePolicy.Minimum, QSizePolicy.Expanding)
		if layout is None:
			layout = infobox.layout()
		layout.addItem(qs, 	layout.rowCount() + 1, 0, 1, 0)

	infobox.exec()

	return infobox
