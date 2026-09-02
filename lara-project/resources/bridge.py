from PySide6.QtCore import QObject, Slot

class MapBridge(QObject):

    def __init__(self, window):
        super().__init__()
        self.window = window

    @Slot(float, float)
    def updateCoordinates(self, lat, lon):
        print("Clicked:", lat, lon)
        self.window.update_coordinates(lat, lon)
