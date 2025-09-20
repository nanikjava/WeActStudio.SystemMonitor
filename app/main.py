import serial.tools.list_ports

_orig_comports = serial.tools.list_ports.comports

def fake_comports():
    ports = list(_orig_comports())
    # Inject fake device
    class FakePort:
        device = "/dev/fakeUSB0"
        name = "fakeUSB0"
        description = "Fake Device AB"
    ports.append(FakePort())
    return ports

serial.tools.list_ports.comports = fake_comports

# Test
for port in serial.tools.list_ports.comports():
    print(port.device, port.description)
