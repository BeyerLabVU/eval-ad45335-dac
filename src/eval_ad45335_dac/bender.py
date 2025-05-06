from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGroupBox, QSlider, QLabel, QPushButton, QVBoxLayout, QSizePolicy, QSpacerItem

from control_box import ChannelsControlBox
from helper import _add_channel_combo, bind_widget_to_state
from eval_ad45335_dac.eval_ad45335_dac_proto import Channel
from state import state
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
        
        bind_widget_to_state(
            self.slider.value,
            self.slider.setValue,
            lambda: state.config.quadrupole_bender,
            "bend",
            self.slider.valueChanged
        )
        

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
        state.config.quadrupole_bender.channels.bend_ions_plus_channel = 100.0 * (float(self.slider.sliderPosition()) / 999.0)
        state.config.quadrupole_bender.channels.bend_ions_minus_channel = -100.0 * (float(self.slider.sliderPosition()) / 999.0)

        # bip_ch = self.voltage_channels[self.controlBox.bip_box.currentIndex()]
        # bip_voltage =  100.0 * (float(self.slider.sliderPosition()) / 999.0)
        # dac.set_voltage(bip_voltage, bip_ch)

        # bim_ch = self.voltage_channels[self.controlBox.bim_box.currentIndex()]
        # bim_voltage = 
        # dac.set_voltage(bim_voltage, bim_ch)
    
        


class BenderControlBox(ChannelsControlBox):
    def __init__(self, name: str, voltage_channels: list[Channel]):
        super().__init__(name, voltage_channels)
        self.bip_box = _add_channel_combo(
            self.options_grid,
            label="Bend ions +: ",
            row=0,
            voltage_channels=voltage_channels,
        )

        self.bim_box = _add_channel_combo(
            self.options_grid,
            label="Bend ions -: ",
            row=1,
            voltage_channels=voltage_channels,
        )
        
        bind_widget_to_state(
            self.bip_box.currentData,
            lambda v: self.bip_box.setCurrentIndex(self.bip_box.findText(f"channel {v.port} on {v.type}")),
            lambda: state.config.quadrupole_bender.channels,
            "bend_ions_plus_channel",
            self.bip_box.currentIndexChanged
        )
        bind_widget_to_state(
            self.bim_box.currentData,
            lambda v: self.bim_box.setCurrentIndex(self.bim_box.findText(f"channel {v.port} on {v.type}")),
            lambda: state.config.quadrupole_bender.channels,
            "bend_ions_minus_channel",
            self.bim_box.currentIndexChanged
        )

