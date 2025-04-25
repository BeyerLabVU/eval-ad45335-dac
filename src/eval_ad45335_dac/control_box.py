from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QGridLayout

class ChannelsControlBox(QGroupBox):
    def __init__(self, name: str, voltage_channels: list):
        super().__init__("Deflector Settings")

        self.name_label = QLabel(name)

        self.layout = QVBoxLayout()
        self.options_grid = QGridLayout()
        self.layout.addWidget(self.name_label)
        self.layout.addLayout(self.options_grid)
        self.setLayout(self.layout)