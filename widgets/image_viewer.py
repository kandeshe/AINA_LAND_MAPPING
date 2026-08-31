from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QScrollArea
)

from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt


class ImageViewer(QWidget):

    def __init__(self):
        super().__init__()

        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignCenter)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.imageLabel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scrollArea)

    def loadImage(self, image_path):

        pixmap = QPixmap(image_path)

        if pixmap.isNull():
            self.imageLabel.setText("Image not found")
            return

        self.imageLabel.setPixmap(pixmap)
