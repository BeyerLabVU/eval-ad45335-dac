import asyncio
import logging
import os
import signal
import time
import uuid
from grpclib.server import Server
from eval_ad45335_dac.eval_ad45335_dac_proto import DacBase, StoredConfig, ChannelConfig, ChannelConfigReply, Config, ConfigReply
from eval_ad45335_dac.eval_ad45335_dac_proto import StoreConfigRequest, GetStoredConfigRequest, Empty, StoredConfigsReply
import tomllib
from arduino_DAC_control import dac

# from deflector import *
# from lens import *
# from bender import *
# from arduino_DAC_control import *
# from gui import *
from state import state

class DacService(DacBase):    
    async def send_channel_config(self, message: ChannelConfig) -> ChannelConfigReply:
        logger.info("Received channel configuration")
        logger.info(message)
        return ChannelConfigReply(success=True, message="Channel configuration updated successfully")
    
    async def send_complete_config(self, message: Config) -> ConfigReply:
        logger.info("Received complete configuration")
        logger.info(message)
        state.config = message
        print(state.config)
        state.state_changed.emit()
        return ConfigReply(success=True, message="Complete configuration updated successfully")
    
    async def store_config(self, message: StoreConfigRequest) -> StoredConfig:
        # time.time() returns the current unix epoch as a float, where the part after the decimal point is smaller than a second.
        # We multiply by 1e3 to get the current unix millisecond epoch as integer
        ts = int(time.time()  * 1e3)
        
        stored_config = StoredConfig(
            timestamp=ts,
            name=message.name,
            uuid=str(uuid.uuid4()),
            config=message.config
        )
        
        # ensure there is a /stored_configs folder:
        os.makedirs("stored_configs", exist_ok=True)
        file_path = f"stored_configs/{stored_config.uuid}"
        # wb = write binary
        with open(file_path, "wb") as f:
            f.write(bytes(stored_config))
        
        return stored_config
    
    async def get_config(self, message: GetStoredConfigRequest) -> StoredConfig:
    
        config = StoredConfig()
        with open(f"stored_configs/{message.uuid}", "rb") as f:
            config = StoredConfig.parse(config, data=f.read())
        
        return config
    
    
    async def get_all_stored_configs(self, message: Empty) -> StoredConfigsReply:
        config_dir = "stored_configs"
        config_list = StoredConfigsReply()
        try:
            for filename in os.listdir(config_dir):
                if not os.path.isfile(os.path.join(config_dir, filename)):
                    continue
                with open(f"stored_configs/{filename}", "rb") as f:
                    stored_config = StoredConfig.parse(StoredConfig(), data=f.read())
                    config_list.configs.append(stored_config)
            return config_list
        except FileNotFoundError:
            logger.warning("File not found!")
            return StoredConfigsReply()
        
        
    async def update_voltages(self, message) -> Empty:
        state.config = message
        
        if state.config.horizontal_bender_einzel != None:
            dac.set_voltage(state.config.horizontal_bender_einzel.channel)
        
        if state.config.post_stack_deflector != None:
            dac.set_voltage(state.config.post_stack_deflector.channels.x_minus_channel)
            dac.set_voltage(state.config.post_stack_deflector.channels.x_plus_channel)
            dac.set_voltage(state.config.post_stack_deflector.channels.z_minus_channel)
            dac.set_voltage(state.config.post_stack_deflector.channels.z_plus_channel)
        
        if state.config.pre_stack_deflector != None:
            dac.set_voltage(state.config.pre_stack_deflector.channels.x_minus_channel)
            dac.set_voltage(state.config.pre_stack_deflector.channels.x_plus_channel)
            dac.set_voltage(state.config.pre_stack_deflector.channels.z_minus_channel)
            dac.set_voltage(state.config.pre_stack_deflector.channels.z_plus_channel)
        
        if state.config.quadrupole_bender != None:
            dac.set_voltage(state.config.quadrupole_bender.channels.bend_ions_minus_channel)
            dac.set_voltage(state.config.quadrupole_bender.channels.bend_ions_plus_channel)    
        
        if state.config.stack_einzel != None:
            dac.set_voltage(state.config.stack_einzel.channel)
    
        return Empty()
    

async def main():
    # Replace this list with your actual service implementations
    server = Server([DacService()])
    
    # We gather the port from the h2pcontrol.server.toml file by default, if we can not get that port we take a default port.
    port = configuration.get("port", 50052)
    await server.start("localhost", port)
    
    logger.info(f"Server started on localhost:{port}")

    # Use an asyncio Event to wait for shutdown signal
    should_stop = asyncio.Event()
    
    # To gracefully handle shutdown
    def _signal_handler():
        logger.info("Shutdown signal received.")
        should_stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    await should_stop.wait()
    logger.info("Shutting down server...")
    await server.close()
    await server.wait_closed()
    logger.info("Server shutdown complete.")

# Default logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- Read configuration from TOML ---
with open("h2pcontrol.server.toml", "rb") as f:
    config = tomllib.load(f)
configuration = config.get("configuration", {})

if __name__ == '__main__':
    asyncio.run(main())
    
