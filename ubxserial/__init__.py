#!/usr/bin/python
#
# ubx packet exchange
#
# Wilfried Klaebe <wk-openmoko@chaos.in-kiel.de>
# Justus Paulick <justus.paulick@tu-dresden.de>
# Kai Geissdoerfer <kai.geissdoerfer@tu-dresden.de>
#
# Usage: ubx-serial [OPTIONS]
#
#  Writes binary config file [CONFIG] to ublox device at [PORT].
#
# Options:
#  -p, --port PATH    Serial port of device  [required]
#  -c, --config PATH  Binary config to send to device  [required]
#  -w, --warn-only    Warn only on read errors
#  -v, --verbose
#  --help             Show this message and exit.
#
# message file will be read line by line (every line should be a UBX-Message)
# message files could be u-center-configuration files or files like the example files (bytes in ascii only)
# the message will be sent to the UBX receiver and the program waits for an answer
# if an UBX-Message is recieved from the UBX receiver as answer the Message will be printed in Bytes
# if there is no answer in timeout the programm will print an information and go to the next line
#
# prepends 0xb5 0x62 header and appends checksum to every Message (Line)
# outputs first answer from ublox-reciver in bytes
#

import sys
import binascii
import time
import serial 
import re
import click
from pathlib import Path
import logging

consoleHandler = logging.StreamHandler()
logger = logging.getLogger("ubxserial")
logger.addHandler(consoleHandler)


def calc_check_sum(cmd: bytes):
    cs0, cs1 = 0, 0
    for byte in cmd:
        cs0 += byte
        cs1 += cs0

    cs0 = (cs0 % 256).to_bytes(1, "little")
    cs1 = (cs1 % 256).to_bytes(1, "little")

    logger.debug(f"Checksum of {cmd} is [{cs0}, {cs1}]")
    return cs0, cs1


def cmd_to_message(cmd: bytes):
    header = b"\xb5\x62"
    cs0, cs1 = calc_check_sum(cmd)
    return header + cmd + cs0 + cs1


class UBXStream(object):
    def __init__(self, port: Path, baudrate: int = 9600, timeout: float = 5):
        self._dev = None
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout

    def __enter__(self):
        self._dev = serial.Serial(
            port=self._port, baudrate=self._baudrate, timeout=self._timeout
        )
        self._dev.flushInput()
        self._dev.flushOutput()
        return self

    def __exit__(self, *exc):
        self._dev.close()

    def write(self, cmd: bytes):
        msg = cmd_to_message(cmd)
        logger.debug(f"Writing {msg} to device")
        self._dev.write(msg)

    def read_pkt(self):
        ts_start = time.time()
        while True:
            if self._dev.read(1) == b"\xb5":
                if self._dev.read(1) == b"\x62":
                    break
            if time.time() > ts_start + self._timeout:
                raise TimeoutError("Timed out waiting for message")

        header = self._dev.read(4)
        logger.debug(f"Read header {header} from device")
        if len(header) < 3:
            raise Exception("received Message too short")

        msg_class, msg_id = header[:2]
        msg_len = int.from_bytes(header[2:], "little", signed=False)
        logger.debug(
            f"Received message with class {msg_class}, ID {msg_id} and length {msg_len} from device"
        )

        msg = self._dev.read(msg_len + 2)
        logger.debug(f"Read msg {msg} from device")

        if len(msg) != (msg_len + 2):
            raise Exception("Message length mismatch")

        payload = msg[:msg_len]
        cs0, cs1 = calc_check_sum(header + payload)

        if not msg[-2].to_bytes(1, "little") == cs0:
            raise Exception(
                f"Checksum mismatch: {msg[-2].to_bytes(1, 'little')}!={cs0}"
            )
        if not msg[-1].to_bytes(1, "little") == cs1:
            raise Exception(
                f"Checksum mismatch: {msg[-1].to_bytes(1, 'little')}!={cs1}"
            )

        return b"\xb5" + b"\x62" + header + msg


@click.command()
@click.option(
    "--port",
    "-p",
    type=click.Path(exists=True),
    required=True,
    help="Serial port of device",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    required=True,
    help="Binary config to send to device",
)
@click.option(
    "--warn-only", "-w", is_flag=True, help="Warn only on read errors",
)
@click.option(
    "--timeout", "-t", 
    type=float, 
    default=5,
    help="read timeout in s. default: 5s",
)
@click.option("-v", "--verbose", count=True, default=2)
def write_config(port, config, warn_only, timeout, verbose):
    """Writes binary config file [CONFIG] to ublox device at [PORT]."""

    if verbose == 0:
        logger.setLevel(logging.ERROR)
    elif verbose == 1:
        logger.setLevel(logging.WARNING)
    elif verbose == 2:
        logger.setLevel(logging.INFO)
    elif verbose > 2:
        logger.setLevel(logging.DEBUG)

    with open(config, "r") as fp, UBXStream(port,9600, timeout) as ubx:
        for i, line in enumerate(fp):
            cmd = re.findall(r"([A-F][0-9]|[A-F][A-F]|[0-9][A-F]|[0-9][0-9])\s", line)# get ubx cmd
            cmd = bytes.fromhex(''.join(cmd))

            ubx.write(cmd)
            logger.info("Sent message to device")

            try:
                reply = None
                reply = ubx.read_pkt()
                logger.info(f"Response: 0x{reply.hex().upper()}")
            except TimeoutError as e:
                logger.error("No reply from device within timeout")
            except Exception as e:
                if warn_only:
                    logger.warn(f"Exception during reading: {str(e)}")
                else:
                    raise

            time.sleep(0.1)


if __name__ == "__main__":
    write_config()
