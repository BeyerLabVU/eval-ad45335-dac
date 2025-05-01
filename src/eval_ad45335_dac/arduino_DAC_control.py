import serial
import serial.tools.list_ports
from time import sleep
import json

from voltage_channel import VoltageChannel

from eval_ad45335_dac_proto import ChannelType, Channel

class arduinoAD45335():
    def __init__(self):
        port_list = serial.tools.list_ports.comports()
        print("Detected COM ports:")
        print("\n".join([p.description for p in port_list]))
        arduino_ports = [
            p.device
            for p in port_list
            if 'Arduino' in p.description  # may need tweaking to match new arduinos
        ]

        if not arduino_ports:
            raise IOError("No Arduino found")
        if len(arduino_ports) > 1:
            warnings.warn('Multiple Arduinos found - using the first')

        self.ser = serial.Serial(arduino_ports[0], baudrate=115200, timeout = 0.1)
        print("Connected to Arduino @", arduino_ports[0])
        print("")

    def send_message(self, message: str):
        # print(message)
        try:
            self.ser.write(f"{message}\n".encode('utf-8'))
            # print(f"{message}\n".encode('utf-8'))
        except Exception as e:
            print(e)

    def readback_binary(self):
        for _ in range(4):
            # print("readback_binary")
            result = self.ser.readline().decode('utf-8')
            print(result[0:-1])

class BipolarAD45335channel(VoltageChannel):
    def __init__(self, channel_number: int, arduino_interface: arduinoAD45335):
        assert((channel_number >= 0) and (channel_number < 32))
        name = f"Ch{channel_number:2d}: AD45335"
        super().__init__(name)
        self.channel = channel_number
        self.interface = arduino_interface

    def set_voltage(self, voltage: float):
        assert(abs(voltage) <= 100.0)
        command_contents = {"command": "SETV", "channel": self.channel, "voltage": voltage}
        msg = json.dumps(command_contents)
        self.interface.send_message(msg)
        self.interface.readback_binary()
        
class DACControl():
    def __init__(self):
        self.AD45335_interface = arduinoAD45335()
                
    def set_voltage(self, voltage: float, channel: Channel):
        assert(abs(voltage) <= 100.0)
        assert((channel.port >= 0) and (channel.port < 32))
                
        ## TODO: Make this use protobuf too instead of json? 
        command_contents = {"command": "SETV", "channel": channel.port, "voltage": voltage}
        msg = json.dumps(command_contents)
        
        if channel.type == ChannelType.AD45335:
            self.AD45335_interface.send_message(msg)
            self.AD45335_interface.readback_binary()
        
dac = DACControl()
