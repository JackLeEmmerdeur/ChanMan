from typing import Optional
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QStyle, QStyleOption, QProxyStyle, QWidget


class TreeViewDropProxyStyle(QProxyStyle):
	def __init__(self):
		super(TreeViewDropProxyStyle, self).__init__()

	def drawPrimitive(
		self,
		element: QStyle.PrimitiveElement,
		option: QStyleOption,
		painter: QPainter,
		widget: Optional[QWidget]
	) -> None:
		if element == QStyle.PE_IndicatorItemViewItemDrop and not option.rect.isNull():
			opt = QStyleOption(option)
			opt.rect.setLeft(0)
			if widget is not None:
				opt.rect.setRight(widget.width())

			super(TreeViewDropProxyStyle, self).drawPrimitive(element, opt, painter, widget)
			return None

		super(TreeViewDropProxyStyle, self).drawPrimitive(element, option, painter, widget)
