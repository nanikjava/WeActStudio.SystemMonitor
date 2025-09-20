import serial
import time
import threading 
import os
import os
import pty
import serial.tools.list_ports

CMD_WHO_AM_I = 0x01  # Establish communication before driving the screen
CMD_SET_ORIENTATION = 0x02  # Sets the screen orientation
CMD_SET_BRIGHTNESS = 0x03  # Sets the screen brightness
CMD_FULL = 0x04  # Displays an image on the screen
CMD_SET_BITMAP = 0x05  # Displays an image on the screen
CMD_ENABLE_HUMITURE_REPORT = 0x06
CMD_FREE = 0x07
CMD_SET_UNCONNECT_BRIGHTNESS = 0x10
CMD_SET_UNCONNECT_ORIENTATION = 0x11
CMD_SET_BITMAP_WITH_FASTLZ = 0x15
CMD_SYSTEM_RESET = 0x40
CMD_SYSTEM_VERSION = 0x42
CMD_SYSTEM_SERIAL_NUM = 0x43
CMD_END = 0x0A  # Displays an image on the screen
CMD_READ = 0x80

def create_fake_tty(name="fakeUSB0", product="AB", vid=0x1234, pid=0x5678):
    master, slave = pty.openpty()
    slave_path = os.ttyname(slave)

    _orig_comports = serial.tools.list_ports.comports

    class FakePort:
        def __init__(self, device, name, description, hwid):
            self.device = device
            self.name = name
            self.description = description
            self.hwid = hwid

        def __getitem__(self, index):
            if index == 0:
                return self.device
            elif index == 1:
                return self.name
            elif index == 2:
                return self.description
            elif index == 3:
                return self.hwid
            raise IndexError

    def fake_comports():
        ports = list(_orig_comports())
        ports.append(FakePort(slave_path, name, f"Fake Device {product}", f"USB VID:PID={vid:04x}:{pid:04x}"))
        return ports

    serial.tools.list_ports.comports = fake_comports

    def simulator():
        while True:
            try:
                # Read command bytes (blocking)
                data = os.read(master, 16)  # read up to 16 bytes
                if not data:
                    time.sleep(0.01)
                    continue

                print("data = " , data)
                # Check for brightness read command
                if len(data) >= 2:
                    cmd = data[0]
                    end_byte = data[1]
                    if (cmd & CMD_READ) and (cmd & 0x7F) == CMD_SET_UNCONNECT_BRIGHTNESS and end_byte == CMD_END:
                        # Prepare a 2-byte response, e.g., brightness 128
                        print("sending response")
                        response = bytes([cmd, 128, end_byte])
                        os.write(master, response)
            except OSError:
                break  # master closed

    t = threading.Thread(target=simulator, daemon=True)
    t.start()

    return slave_path, t