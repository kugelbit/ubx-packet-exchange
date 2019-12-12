import time
import pytest
import serial

from ubxserial import UBXStream
from ubxserial import calc_check_sum
from ubxserial import cmd_to_message


class FakeSerial(object):
    def __init__(self, port, baudrate, timeout=0.1):
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def open(self):
        pass

    def close(self):
        pass

    def write(self, msg):
        pass

    def flushInput(self):
        pass

    def flushOutput(self):
        pass

    def read(self, n_bytes):
        data = bytes.fromhex("b56204deadbeef3cfe")
        return data


@pytest.fixture
def payload():
    return bytes([0x06, 0x04, 0x04, 0x00, 0xFF, 0x87, 0x00, 0x00])


def test_checksum(payload):
    cs0, cs1 = calc_check_sum(payload)
    assert cs0 == bytes.fromhex("94")
    assert cs1 == bytes.fromhex("F5")


def test_cmd_to_message(payload):
    msg = cmd_to_message(payload)
    assert msg[0] == 0xB5
    assert msg[1] == 0x62
    for i in range(2, 2 + len(payload)):
        assert msg[i] == payload[i - 2]

    cs0, cs1 = calc_check_sum(payload)
    assert msg[-2].to_bytes(1, "little") == cs0
    assert msg[-1].to_bytes(1, "little") == cs1


def test_instantiation(monkeypatch):
    monkeypatch.setattr(serial, "Serial", FakeSerial)
    with UBXStream("/dev/ttyUSB0") as ubx:
        pass


def test_read(monkeypatch):
    monkeypatch.setattr(serial, "Serial", FakeSerial)
    with UBXStream("/dev/ttyUSB0") as ubx:
        data = ubx.read()
        assert data == bytes.fromhex("deadbeef")


def test_write(monkeypatch):
    monkeypatch.setattr(serial, "Serial", FakeSerial)
    with UBXStream("/dev/ttyUSB0") as ubx:
        ubx.write(bytes.fromhex("deadbeef"))


def test_write(monkeypatch):
    monkeypatch.setattr(serial, "Serial", FakeSerial)
    with UBXStream("/dev/ttyUSB0") as ubx:
        ubx.write(bytes.fromhex("deadbeef"))
