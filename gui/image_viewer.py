from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QFont, QColor
from PySide6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsTextItem)


class ImageViewer(QGraphicsView):
    """
    自定义图片查看器 (稳健修复版)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # 基础设置
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setFrameShape(QGraphicsView.NoFrame)

        self.current_pixmap_item = None
        self.show_welcome()

    def clear_content(self):
        self.scene.clear()
        self.current_pixmap_item = None
        self.resetTransform()

    def show_welcome(self):
        self.clear_content()
        self._draw_centered_text("👋\n\n请在左侧导入文件\n并点击“开始生成”", color="#CCCCCC", font_size=16)

    def set_image(self, qpixmap):
        self.clear_content()
        self.current_pixmap_item = self.scene.addPixmap(qpixmap)
        self.fitInView(self.current_pixmap_item, Qt.KeepAspectRatio)
        self.scene.setSceneRect(self.current_pixmap_item.boundingRect())
        self.viewport().update()  # 强制刷新

    def _draw_centered_text(self, text, color="#333333", font_size=14):
        item = QGraphicsTextItem(text)
        font = QFont("Microsoft YaHei", font_size)
        font.setBold(True)
        item.setFont(font)
        item.setDefaultTextColor(QColor(color))

        rect = item.boundingRect()
        item.setPos(-rect.width() / 2, -rect.height() / 2)
        self.scene.addItem(item)
        self.scene.setSceneRect(-200, -200, 400, 400)

    def wheelEvent(self, event):
        if not self.current_pixmap_item: return
        angle = event.angleDelta().y()
        factor = 1.15 if angle > 0 else 1 / 1.15
        curr_scale = self.transform().m11()
        if curr_scale < 0.05 and factor < 1: return
        if curr_scale > 50 and factor > 1: return
        self.scale(factor, factor)