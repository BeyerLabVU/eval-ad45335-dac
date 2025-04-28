import sys
from PySide6.QtCore import QTimer, QObject, QThread, Signal
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QApplication, QVBoxLayout, QLabel, QWidget, QSlider, QPushButton, QHBoxLayout, QGroupBox, QSpacerItem, QSizePolicy, QTabWidget, QGridLayout, QComboBox, QScrollArea, QFormLayout

from deflector import *
from lens import *
from bender import *
from arduino_DAC_control import *
from state import state

from eval_ad45335_dac.eval_ad45335_dac import StoredConfigRequest, GetStoredConfigRequest


class VoltageUpdateWorker(QObject):
    update_finished = Signal()

    def __init__(self, control_widgets):
        super().__init__()
        self.control_widgets = control_widgets

    def run(self):
        # print("\nUpdating voltages:")
        for widget in self.control_widgets:
            widget.update_voltages()
        # print("Voltage update finished!")
        self.update_finished.emit()

class MainWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.state = state
        self.DACControl = DACControl()

        self.init_voltage_channels()

        self.tab_widget = QTabWidget()

        # Main control tab
        self.control_tab = QWidget()
        self.setup_control_tab()

        # Channel assignment tab
        self.channel_tab = QScrollArea()
        self.channel_tab.setWidgetResizable(True)
        self.channel_content_widget = QWidget()
        self.channel_layout = QFormLayout(self.channel_content_widget)
        self.channel_tab.setWidget(self.channel_content_widget)
        self.setup_channel_tab()

        self.tab_widget.addTab(self.control_tab, "Controls")

        self.tab_widget.addTab(self.channel_tab, "Channel Settings")

        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.start_voltage_update)
        self.update_timer.start(300)

        self.update_thread = None
        self.update_worker = None
        self.is_updating = False
        print("lets show!")

    def init_voltage_channels(self):
        self.voltage_channels = []
        for ch in range(32):
            self.voltage_channels.append(Channel(ch, ChannelType.AD45335))

    def setup_control_tab(self):
        """Setup the first tab with main control widgets."""
        self.control_widgets = [
            # Need to make these state_objects getters with a lambda to ensure its not an old reference when we update state
            DeflectionAngleWidget("Pre-Stack Deflector", lambda: self.state.config.pre_stack_deflector, self.voltage_channels),
            # FocusControlWidget("Stack Einzel", self.voltage_channels),
            DeflectionAngleWidget("Post-Stack Deflector", lambda: self.state.config.post_stack_deflector, self.voltage_channels),
            # FocusControlWidget("Horz. Bender Einzel", self.voltage_channels),
            BenderControlWidget("Quadrupole Bender", self.voltage_channels)
        ]

        self.update_button = QPushButton("Update Voltages")
        self.update_button.clicked.connect(self.start_voltage_update)

        self.save_button = QPushButton("Save config")
        # Use a lambda to defer calling store_config until the button is actually clicked, instead of calling it immediately during setup.
        self.save_button.clicked.connect(lambda: self.state.store_config(StoredConfigRequest("tryout")))

        self.read_config_button = QPushButton("Read config")
        self.read_config_button.clicked.connect(lambda: self.read_config())

        self.top_layout = QVBoxLayout()

        layout = QHBoxLayout()
        for widget in self.control_widgets:
            layout.addWidget(widget)

        self.top_layout.addLayout(layout)
        self.top_layout.addWidget(self.update_button)
        self.top_layout.addWidget(self.save_button)
        self.top_layout.addWidget(self.read_config_button)

        self.top_layout.addStretch(1)
        self.control_tab.setLayout(self.top_layout)

    def read_config(self):
        self.state.get_config(GetStoredConfigRequest("96448ec1-cb80-48ec-8d04-88de139bc7d3"))
                

    def start_voltage_update(self):
        if self.is_updating:
            return  # Avoid starting a new thread while one is running

        self.is_updating = True

        # Initialize the worker and thread
        self.update_worker = VoltageUpdateWorker(self.control_widgets)
        self.update_thread = QThread()
        self.update_worker.moveToThread(self.update_thread)

        # Connect signals and slots
        self.update_thread.started.connect(self.update_worker.run)
        self.update_worker.update_finished.connect(self.update_thread.quit)
        self.update_worker.update_finished.connect(self.update_worker.deleteLater)
        self.update_worker.update_finished.connect(self.finish_voltage_update)
        self.update_thread.finished.connect(self.update_thread.deleteLater)

        self.update_thread.start()

    def finish_voltage_update(self):
        self.is_updating = False

    def setup_channel_tab(self):
        """Setup the second tab with channel settings."""
        for widget in self.control_widgets:
            self.channel_layout.addRow(widget.controlBox)


if __name__ == '__main__':

    app = QApplication(sys.argv)
    main_widget = MainWidget()
    main_widget.show()
    sys.exit(app.exec())
