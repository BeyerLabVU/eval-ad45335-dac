from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGroupBox, QSlider, QLabel, QPushButton, QVBoxLayout, QSizePolicy, QComboBox, QSpacerItem

from control_box import ChannelsControlBox
from voltage_channel import VoltageChannel

class BenderControlWidget(QGroupBox):
    def __init__(self, name: str, voltage_channels: list):
        super().__init__("Bending")
        super().setMinimumHeight(350)
        super().setMaximumHeight(350)
        super().setMinimumWidth(100)
        super().setMaximumWidth(100)

        self.voltage_channels = voltage_channels
        self.controlBox = BenderControlBox(name, voltage_channels)

        self.slider = QSlider(Qt.Vertical)
        self.slider.setMinimum(0)
        self.slider.setMaximum(999)
        self.slider.setValue(0)
        self.slider.setMinimumHeight(150)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setTickInterval(10)

        self.name_label = QLabel(name)
        self.label = QLabel("Bend Str.:  0")
        self.lock_button = QPushButton("Lock bend")
        self.lock_button.setCheckable(True)
        self.lock_button.toggled.connect(self.toggle_lock)

        self.locked = False

        # Customize the slider appearance
        self.slider.setStyleSheet(
            "QSlider::groove:vertical {"
            "    background: white;"
            "    border: 2px solid black;"
            "    width: 10px;"
            "}"
            "QSlider::handle:vertical {"
            "    background: red;"
            "    border: 2px solid black;"
            "    height: 10px;"
            "    margin: 0 -3px;"
            "}"
        )

        self.slider.valueChanged.connect(self.update_label)

        self.vspace1 = QSpacerItem(10, 23, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.vspace2 = QSpacerItem(10, 23, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.layout = QVBoxLayout()
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.addWidget(self.name_label)
        self.layout.addItem(self.vspace1)
        self.layout.addWidget(self.slider, alignment=Qt.AlignCenter)
        self.layout.addItem(self.vspace2)
        self.layout.addWidget(self.label, alignment=Qt.AlignCenter)
        self.layout.addStretch(1)
        self.layout.addWidget(self.lock_button)
        self.setLayout(self.layout)

    def update_label(self, value):
        if not self.locked:
            self.label.setText(f"Bend Str.: {value:4d}")

    def toggle_lock(self, checked):
        self.locked = checked
        if checked:
            self.lock_button.setText("Unlock bend")
        else:
            self.lock_button.setText("Lock bend")

    def set_trigger_value(self, value):
        if not self.locked:
            self.slider.setValue(value)

    def update_voltages(self):
        bip_ch = self.voltage_channels[self.controlBox.bip_box.currentIndex()]
        bip_voltage =  100.0 * (float(self.slider.sliderPosition()) / 999.0)
        bip_ch.set_voltage(bip_voltage)

        bim_ch = self.voltage_channels[self.controlBox.bim_box.currentIndex()]
        bim_voltage = -100.0 * (float(self.slider.sliderPosition()) / 999.0)
        bim_ch.set_voltage(bim_voltage)


class BenderControlBox(ChannelsControlBox):
    def __init__(self, name: str, voltage_channels: list):
        super().__init__(name, voltage_channels)

        self.options_grid.addWidget(QLabel("Bend ions +: "), 0, 0)
        self.bip_box = QComboBox()
        self.bip_box.addItems([vch.name for vch in voltage_channels])
        self.options_grid.addWidget(self.bip_box, 0, 1)

        self.options_grid.addWidget(QLabel("Bend ions -: "), 1, 0)
        self.bim_box = QComboBox()
        self.bim_box.addItems([vch.name for vch in voltage_channels])
        self.options_grid.addWidget(self.bim_box, 1, 1)