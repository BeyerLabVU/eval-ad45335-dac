from typing import Callable
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QGroupBox, QLabel, QSlider, QHBoxLayout, QPushButton

from control_box import *
from helper import _add_channel_combo, bind_widget_to_state
from eval_ad45335_dac.eval_ad45335_dac_proto import StackDeflector
from joystick import *

class DeflectionControlBox(ChannelsControlBox):
    def __init__(self, name: str, state_object_getter: Callable[[], StackDeflector], voltage_channels: list):
        super().__init__(name, voltage_channels)
        self.xp_box = _add_channel_combo(
            self.options_grid,
            label="x+ ch: ",
            row=0,
            voltage_channels=voltage_channels,
        )
        
        self.xm_box = _add_channel_combo(
            self.options_grid,
            label="x- ch: ",
            row=1,
            voltage_channels=voltage_channels,
        )
        
        self.zp_box = _add_channel_combo(
            self.options_grid,
            label="z+ ch: ",
            row=2,
            voltage_channels=voltage_channels,
        )
        
        self.zm_box = _add_channel_combo(
            self.options_grid,
            label="z- ch: ",
            row=3,
            voltage_channels=voltage_channels,
        )
    
        
        bind_widget_to_state(
            self.xm_box.currentData,
            lambda v: self.xm_box.setCurrentIndex(self.xm_box.findText(f"channel {v.port} on {v.type}")),
            lambda: state_object_getter().channels,
            "x_minus_channel",
            self.xm_box.currentIndexChanged
        )
        
        bind_widget_to_state(
            self.xp_box.currentData,
            lambda v: self.xp_box.setCurrentIndex(self.xp_box.findText(f"channel {v.port} on {v.type}")),
            lambda: state_object_getter().channels,
            "x_plus_channel",
            self.xp_box.currentIndexChanged
        )
        
        bind_widget_to_state(
            self.zm_box.currentData,
            lambda v: self.zm_box.setCurrentIndex(self.zm_box.findText(f"channel {v.port} on {v.type}")),
            lambda: state_object_getter().channels,
            "z_minus_channel",
            self.zm_box.currentIndexChanged
        )
        
        bind_widget_to_state(
            self.zp_box.currentData,
            lambda v: self.zp_box.setCurrentIndex(self.zp_box.findText(f"channel {v.port} on {v.type}")),
            lambda: state_object_getter().channels,
            "z_plus_channel",
            self.zp_box.currentIndexChanged
        )



class DeflectionAngleWidget(QGroupBox):
    def __init__(self, name: str, state_object_getter : Callable[[], StackDeflector], voltage_channels: list):
        super().__init__("Deflection Angle")
        super().setMinimumHeight(350)
        super().setMaximumHeight(350)
        super().setMinimumWidth(200)
        super().setMaximumWidth(200)
        
        self.state_object_getter = state_object_getter
        self.voltage_channels = voltage_channels
        self.controlBox = DeflectionControlBox(name, state_object_getter, self.voltage_channels)

        # Initialize pygame for joystick handling
        # pygame.init()
        # pygame.joystick.init()
        # self.joystick = None
        # if pygame.joystick.get_count() > 0:
        #     self.joystick = pygame.joystick.Joystick(0)
        #     self.joystick.init()
        self.joystick = None

        # Create UI elements
        self.name_label = QLabel(name)

        self.label = QLabel("Deflection Setting: (0.000, 0.000)")
        self.circle_widget = JoystickCircleWidget(self.label)

        self.dead_zone_label = QLabel("Dead Zone: 0.2")
        self.dead_zone_slider = QSlider(Qt.Horizontal)
        self.dead_zone_slider.setMinimum(0)
        self.dead_zone_slider.setMaximum(100)
        self.dead_zone_slider.setValue(20)
        self.dead_zone_slider.setSingleStep(1)
        self.dead_zone_slider.valueChanged.connect(self.update_dead_zone)
        self.dead_zone_slider.setMinimumWidth(100)

        self.sensitivity_label = QLabel("Sensitivity:   1.00")
        self.sensitivity_slider = QSlider(Qt.Horizontal)
        self.sensitivity_slider.setMinimum(10)  # 0.1
        self.sensitivity_slider.setMaximum(300)  # 3.0
        self.sensitivity_slider.setValue(100)  # Default to 1.0
        self.sensitivity_slider.valueChanged.connect(self.update_sensitivity)
        self.sensitivity_slider.setMinimumWidth(100)

        self.lock_button = QPushButton("Lock Angle")
        self.lock_button.setCheckable(True)
        self.lock_button.toggled.connect(self.toggle_lock_position)

        # Connect joystick wheel signal to sensitivity slider adjustment
        self.circle_widget.wheelScrolled.connect(self.adjust_sensitivity_slider)

        # Layout setup
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        layout.addWidget(self.name_label)
        layout.addWidget(self.circle_widget, stretch=1)
        layout.addWidget(self.label)

        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.dead_zone_label)
        slider_layout.addWidget(self.dead_zone_slider)
        layout.addLayout(slider_layout)

        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(self.sensitivity_label)
        sensitivity_layout.addWidget(self.sensitivity_slider)
        layout.addLayout(sensitivity_layout)

        layout.addWidget(self.lock_button)
        self.setLayout(layout)

        # Timer to poll joystick data
        self.timer = QTimer()
        self.timer.timeout.connect(self.poll_joystick)
        self.timer.start(16)  # ~60 FPS

        # self.last_time = pygame.time.get_ticks()
        self.dead_zone = 0.2
        self.sensitivity = 1.0
    
          
        bind_widget_to_state(
            self.dead_zone_slider.value,
            self.dead_zone_slider.setValue,
            lambda: state_object_getter(),
            "dead_zone",
            self.dead_zone_slider.valueChanged
        )
        bind_widget_to_state(
            self.sensitivity_slider.value,
            self.sensitivity_slider.setValue,
            lambda: state_object_getter(),
            "sensitivity",
            self.sensitivity_slider.valueChanged
        )
        bind_widget_to_state(
            lambda: self.circle_widget.position_x,
            self.circle_widget.set_position_x,
            lambda: state_object_getter().deflection_setting,
            "x",
            self.circle_widget.xChanged
        )
        bind_widget_to_state(
            lambda: self.circle_widget.position_y,
            self.circle_widget.set_position_y,
            lambda: state_object_getter().deflection_setting,
            "z",
            self.circle_widget.yChanged
        )

    def adjust_sensitivity_slider(self, delta):
        """Adjust the sensitivity slider based on the mouse wheel."""
        new_value = self.sensitivity_slider.value() + delta
        self.sensitivity_slider.setValue(max(self.sensitivity_slider.minimum(), min(self.sensitivity_slider.maximum(), new_value)))

    def update_dead_zone(self, value):
        self.dead_zone = value / 100.0
        self.dead_zone_label.setText(f"Dead Zone: {value / 100.0:2.2f}")

    def update_sensitivity(self, value):
        self.sensitivity = value
        self.circle_widget.wheel_sensitivity = self.sensitivity / 10
        self.sensitivity_label.setText(f"Sensitivity: {self.sensitivity / 10:6.2f}")

    def toggle_lock_position(self, checked):
        if checked:
            self.circle_widget.lock_position()
            self.lock_button.setText("Unlock Angle")
        else:
            self.circle_widget.unlock_position()
            self.lock_button.setText("Lock Angle")

    def poll_joystick(self):
        if self.joystick is None:
            return

        pygame.event.pump()

        x = self.joystick.get_axis(0)  # Left joystick X
        y = self.joystick.get_axis(1)  # Left joystick Y
        trigger = self.joystick.get_axis(2)  # Left trigger

        # Normalize joystick values to 1
        magnitude = (x ** 2 + y ** 2) ** 0.5
        if magnitude > 1.0:
            x /= magnitude
            y /= magnitude

        # Apply dead zone
        if abs(x) < self.dead_zone:
            x = 0
        if abs(y) < self.dead_zone:
            y = 0

        # Calculate time delta for integral scaling
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - self.last_time) / 1000.0  # Convert ms to seconds
        self.last_time = current_time

        # Scale joystick input to movement speed with sensitivity
        speed = 100 * self.sensitivity  # Pixels per second at max joystick deflection
        dx = x * speed * delta_time
        dy = -y * speed * delta_time  # Invert Y-axis

        # Update circle position
        self.circle_widget.update_position(dx, dy)

        # Update trigger control
        if self.joystick.get_numaxes() > 2:
            normalized_trigger = int((trigger + 1) / 2 * 100)  # Normalize to 0-100
            main_widget.trigger_control.set_trigger_value(normalized_trigger)

    def update_voltages(self):
        stack_deflector: StackDeflector = self.state_object_getter()
        
        stack_deflector.channels.x_minus_channel.voltage = 100.0 * (self.circle_widget.position_x / self.circle_widget.radius)
        stack_deflector.channels.x_plus_channel.voltage = -100.0 * (self.circle_widget.position_x / self.circle_widget.radius)
        stack_deflector.channels.z_minus_channel.voltage = 100.0 * (self.circle_widget.position_y / self.circle_widget.radius)
        stack_deflector.channels.z_plus_channel.voltage = -100.0 * (self.circle_widget.position_y / self.circle_widget.radius)


    def closeEvent(self, event):
        # Clean up pygame resources
        pygame.quit()
        super().closeEvent(event)