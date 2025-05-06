from eval_ad45335_dac.eval_ad45335_dac_proto import Config, QuadrupoleBender, QuadrupoleBenderChannels, Channel
from eval_ad45335_dac.eval_ad45335_dac_proto import StackDeflector, Einzel, DeflectionSetting, DeflectorChannels
from eval_ad45335_dac.eval_ad45335_dac_proto import StoreConfigRequest, StoredConfig, GetStoredConfigRequest
import os
import time
import uuid
from PySide6.QtCore import QObject, Signal

class State(QObject):
    state_changed = Signal()
    
    
    def __init__(self):
      super().__init__()
      self.config = Config(
        pre_stack_deflector=StackDeflector(
          DeflectionSetting(),
          DeflectorChannels()
        ),
        stack_einzel=Einzel(channel=Channel()),
        post_stack_deflector=StackDeflector(
          DeflectionSetting(),
          DeflectorChannels()
        ),
        horizontal_bender_einzel=Einzel(channel=Channel()),
        quadrupole_bender=QuadrupoleBender(
          channels=QuadrupoleBenderChannels(
            bend_ions_minus_channel=Channel(),
            bend_ions_plus_channel=Channel()
          )
        )
      )
      
    def store_config(self, message: StoreConfigRequest) -> StoredConfig:
        # time.time() returns the current unix epoch as a float, where the part after the decimal point is smaller than a second.
        # We multiply by 1e3 to get the current unix millisecond epoch as integer
        ts = int(time.time()  * 1e3)
        
        print(self.config)
        stored_config = StoredConfig(
            timestamp=ts,
            name=message.name,
            uuid=str(uuid.uuid4()),
            config=self.config
        )
        
        # ensure there is a /stored_configs folder:
        os.makedirs("stored_configs", exist_ok=True)
        file_path = f"stored_configs/{stored_config.uuid}"
        # wb = write binary
        with open(file_path, "wb") as f:
            f.write(bytes(stored_config))
        
        # print(stored_config)
        return stored_config
      
    def set_config(self, message: StoredConfig):
      self.config = message.config
      self.state_changed.emit()
      
    def get_config(self, message: GetStoredConfigRequest) -> StoredConfig:
      stored_config = StoredConfig()
      with open(f"stored_configs/{message.uuid}", "rb") as f:
          stored_config = StoredConfig.parse(stored_config, data=f.read())
      
      print(self.config)
      self.config = stored_config.config
      print(self.config)
      self.state_changed.emit()
      return stored_config
       
    
      
state = State() 