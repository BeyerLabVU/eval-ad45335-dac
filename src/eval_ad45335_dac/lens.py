from typing import Callable
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGroupBox, QSlider, QLabel, QPushButton, QVBoxLayout, QSizePolicy, QComboBox, QSpacerItem

from control_box import ChannelsControlBox
from eval_ad45335_dac.eval_ad45335_dac_proto import Einzel
from helper import bind_widget_to_state, _add_channel_combo
from state import state
from arduino_DAC_control import dac

class FocusControlWidget(QGroupBox):
    def __init__(self, name: str, state_object_getter: Callable[[], Einzel], voltage_channels: list):
        super().__init__("Focusing")
        super().setMinimumHeight(350)
        super().setMaximumHeight(350)
        super().setMinimumWidth(100)
        super().setMaximumWidth(100)

        self.state_object_getter = state_object_getter
        self.voltage_channels = voltage_channels
        self.controlBox = FocusControlBox(name, state_object_getter, voltage_channels)

        self.slider = QSlider(Qt.Vertical)
        self.slider.setMinimum(0)
        self.slider.setMaximum(999)
        self.slider.setValue(0)
        self.slider.setMinimumHeight(150)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setTickInterval(10)

        self.name_label = QLabel(name)
        self.label = QLabel("Focus Str.:  0")
        self.lock_button = QPushButton("Lock Focus")
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
            lambda: state_object_getter(),
            "focus",
            self.slider.valueChanged
        )
 

    def update_label(self, value):
        if not self.locked:
            self.label.setText(f"Focus Str.: {value:4d}")

    def toggle_lock(self, checked):
        self.locked = checked
        if checked:
            self.lock_button.setText("Unlock Focus")
        else:
            self.lock_button.setText("Lock Focus")

    def set_trigger_value(self, value):
        if not self.locked:
            self.slider.setValue(value)

    def update_voltages(self):     
        einzel = self.state_object_getter()
        einzel.channel.voltage = 100.0 * (float(self.slider.sliderPosition()) / 999.0)



class FocusControlBox(ChannelsControlBox):
    def __init__(self, name: str, state_object_getter: Callable[[], Einzel], voltage_channels: list):
        super().__init__(name, voltage_channels)
        
        self.focus_box = _add_channel_combo(
            self.options_grid,
            label="focus ch: ",
            row=1,
            voltage_channels=voltage_channels,
        )
        
        
        bind_widget_to_state(
            self.focus_box.currentData,
            lambda v: self.focus_box.setCurrentIndex(self.focus_box.findText(f"channel {v.port} on {v.type}")),
            lambda: state_object_getter(),
            "channel",
            self.focus_box.currentIndexChanged
        )
        # self.options_grid.addWidget(QLabel("focus ch: "), 0, 0)
        # self.focus_box = QComboBox()
        # self.focus_box.addItems([vch.name for vch in voltage_channels])
        # self.options_grid.addWidget(self.focus_box, 0, 1)