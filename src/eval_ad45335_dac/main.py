import asyncio
import datetime
import logging
import os
import signal
import time
import uuid
import betterproto2
from grpclib.server import Server
from eval_ad45335_dac.eval_ad45335_dac import DacBase, Voltage, VoltageReply, StoredConfig, ChannelConfig, ChannelConfigReply, Config, ConfigReply
from eval_ad45335_dac.eval_ad45335_dac import StoredConfigRequest, GetStoredConfigRequest
import tomllib

class DacService(DacBase):    
    def __init__(self):
        self.config: Config = Config()
    
    async def send_voltage(self, message: Voltage) -> VoltageReply:
        response = VoltageReply(wattage=message.voltage * 2)
        return response
    
    async def send_channel_config(self, message: ChannelConfig) -> ChannelConfigReply:
        logger.info(f"Received channel configuration")
        logger.info(message.pre_stack_deflector_channels.x_minus_channel.type)
        return ChannelConfigReply(success=True, message="Channel configuration updated successfully")
    
    async def send_complete_config(self, message: Config) -> ConfigReply:
        logger.info(f"Received complete configuration")
        logger.info(message)
        self.config = message
        return ConfigReply(success=True, message="Complete configuration updated successfully")
    
    async def store_config(self, message: StoredConfigRequest) -> StoredConfig:
        # time.time() returns the current unix epoch as a float, where the part after the decimal point is smaller than a second.
        # We multiply by 1e3 to get the current unix millisecond epoch as integer
        ts = int(time.time()  * 1e3)
        
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
        
        return stored_config
    
    async def get_config(self, message: GetStoredConfigRequest) -> StoredConfig:
    
        config = StoredConfig()
        with open(f"stored_configs/{message.uuid}", "rb") as f:
            config = StoredConfig.parse(config, data=f.read())
        
        return config
       
    

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
