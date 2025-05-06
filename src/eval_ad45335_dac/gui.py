import asyncio
import sys
from PySide6.QtCore import QTimer, QObject, QThread, Signal
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QVBoxLayout, QLabel, QWidget, QLineEdit, QPushButton, QHBoxLayout, QGroupBox, QSpacerItem, QSizePolicy, QTabWidget, QGridLayout, QComboBox, QScrollArea, QFormLayout
from qasync import QApplication, QEventLoop, asyncSlot

from deflector import *
from lens import *
from bender import *
from arduino_DAC_control import *
from state import state
# from server import main
from eval_ad45335_dac.eval_ad45335_dac_proto import StoreConfigRequest, GetStoredConfigRequest, StoredConfig
from h2pcontrol.h2pcontrol_connector import H2PControl

from eval_ad45335_dac.eval_ad45335_dac_proto import DacStub, Empty, StoredConfigsReply


class VoltageUpdateWorker(QObject):
    update_finished = Signal()

    def __init__(self, control_widgets, dac_server: DacStub):
        self.dac_server = dac_server
        super().__init__()
        self.control_widgets = control_widgets


    def run(self):
        asyncio.create_task(self._async_run())

    async def _async_run(self):
        try: 
            for widget in self.control_widgets:
                widget.update_voltages()
            await self.dac_server.update_voltages(state.config)
        except Exception as e:
            print(f"Error during voltage update: {e}")
        finally:
            self.update_finished.emit()
        

class MainWidget(QWidget):
    def  __init__(self):
        super().__init__()
        
        # Setup h2pcontrol connection
        self.h2pcontroller = H2PControl("localhost:50051")
        self.dac_server = None
        self.setup_connection()
    
        
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

    @asyncSlot()
    async def setup_connection(self):
        await self.h2pcontroller.connect()
        _, self.dac_server = await self.h2pcontroller.register_server(self.h2pcontroller.servers.eval_ad45335_dac_proto, DacStub)
        
        self.setup_config_dropdown()

        
    def init_voltage_channels(self):
        self.voltage_channels = []
        for ch in range(32):
            self.voltage_channels.append(Channel(ch, ChannelType.AD45335))

    def setup_control_tab(self):
        """Setup the first tab with main control widgets."""
        self.control_widgets = [
            # Need to make these state_objects getters with a lambda to ensure its not an old reference when we update state
            DeflectionAngleWidget("Pre-Stack Deflector", lambda: state.config.pre_stack_deflector, self.voltage_channels),
            FocusControlWidget("Stack Einzel", lambda: state.config.stack_einzel, self.voltage_channels),
            DeflectionAngleWidget("Post-Stack Deflector", lambda: state.config.post_stack_deflector, self.voltage_channels),
            FocusControlWidget("Horz. Bender Einzel", lambda: state.config.horizontal_bender_einzel, self.voltage_channels),
            BenderControlWidget("Quadrupole Bender", self.voltage_channels)
        ]

        self.update_button = QPushButton("Update Voltages")
        self.update_button.clicked.connect(self.start_voltage_update)

        # Saving
        self.save_layout = QHBoxLayout()
        self.save_name_input = QLineEdit()
        self.save_name_input.setPlaceholderText("Enter config name")
        
        self.save_button = QPushButton("Save config")
        self.save_button.clicked.connect(lambda: self.save_config(name = self.save_name_input.text()))

        self.save_layout.addWidget(self.save_button)
        self.save_layout.addWidget(self.save_name_input)

        # Reading
        self.read_layout = QHBoxLayout()
        self.read_config_button = QPushButton("Read config")
        self.read_config_button.clicked.connect(lambda: self.read_config())

        self.config_label = QLabel("Stored configurations")
        self.config_combo = QComboBox()
        
        self.read_layout.addWidget(self.config_label)
        self.read_layout.addWidget(self.config_combo)
        self.read_layout.addWidget(self.read_config_button)
        
        self.top_layout = QVBoxLayout()

        layout = QHBoxLayout()
        for widget in self.control_widgets:
            layout.addWidget(widget)

        self.top_layout.addLayout(layout)
        self.top_layout.addWidget(self.update_button)
        self.top_layout.addLayout(self.save_layout)
    
        self.top_layout.addLayout(self.read_layout)
        self.top_layout.addStretch(1)
        
        self.control_tab.setLayout(self.top_layout)
        

    @asyncSlot()
    async def setup_config_dropdown(self):
        stored_configs: StoredConfigsReply = await self.dac_server.get_all_stored_configs(Empty())
        self.config_combo.clear()
        for config in stored_configs.configs:
            self.config_combo.addItem(config.name, config.uuid)

    @asyncSlot()
    async def read_config(self):
        config: StoredConfig = await self.dac_server.get_config(message=GetStoredConfigRequest(self.config_combo.currentData()))
        state.set_config(config)
        
    @asyncSlot()
    async def save_config(self, name: str):     
        await self.dac_server.store_config(StoreConfigRequest(name=name, config=state.config))
        await self.setup_config_dropdown()

    def start_voltage_update(self):
        if self.is_updating:
            return  # Avoid starting a new thread while one is running

        self.is_updating = True
        self.update_worker = VoltageUpdateWorker(self.control_widgets, self.dac_server)
        self.update_worker.update_finished.connect(self.finish_voltage_update)
        self.update_worker.update_finished.connect(self.update_worker.deleteLater)
        
        self.update_worker.run()
        
        # # Start the async operation
        # # Initialize the worker and thread
        # self.update_worker = VoltageUpdateWorker(self.control_widgets, self.dac_server)
        # self.update_thread = QThread()
        # self.update_worker.moveToThread(self.update_thread)

        # # Connect signals and slots
        # self.update_thread.started.connect(self.update_worker.run)
        # self.update_worker.update_finished.connect(self.update_thread.quit)
        # self.update_worker.update_finished.connect(self.update_worker.deleteLater)
        # self.update_worker.update_finished.connect(self.finish_voltage_update)
        # self.update_thread.finished.connect(self.update_thread.deleteLater)

        # self.update_thread.start()

    def finish_voltage_update(self):
        self.is_updating = False

    def setup_channel_tab(self):
        """Setup the second tab with channel settings."""
        for widget in self.control_widgets:
            self.channel_layout.addRow(widget.controlBox)

        
if __name__ == '__main__':

    # Setup the event loop for async calls to api!
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    main_widget = MainWidget()
    main_widget.show()
    
    with loop:
        loop.run_forever()
