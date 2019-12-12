#!/usr/bin/python
#
# ubx packet exchange
#
# Wilfried Klaebe <wk-openmoko@chaos.in-kiel.de>
# Justus Paulick <justus.paulick@tu-dresden.de>
# Kai Geissdoerfer <kai.geissdoerfer@tu-dresden.de>
#
# Usage:
#
# ubxgen.py <message file> <serial port>
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

    def read(self):
        header = self._dev.read(3)
        logger.debug(f"Read {header} from device")

        if len(header) == 0:
            return
        elif len(header) < 3:
            raise Exception("Message too short")

        if header[0] != 0xB5 or header[1] != 0x62:
            raise Exception("Invalid header")

        payload_len = header[2]
        logger.debug(f"Received message with length {payload_len} from device")

        msg = self._dev.read(payload_len + 2)
        logger.debug(f"Read {msg} from device")

        if len(msg) != (payload_len + 2):
            raise Exception("Message length mismatch")

        cs0, cs1 = calc_check_sum(msg[:payload_len])
        payload = msg[:payload_len]

        test0 = msg[-2].to_bytes(1, "little") == cs0
        test1 = msg[-1].to_bytes(1, "little") == cs1

        print(cs0, cs1)
        if not test0 or not test1:
            raise Exception("Checksum mismatch")

        return payload


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
@click.option("-v", "--verbose", count=True, default=2)
def write_config(port, config, warn_only, verbose):
    """Writes binary config file [CONFIG] to ublox device at [PORT]."""

    if verbose == 0:
        logger.setLevel(logging.ERROR)
    elif verbose == 1:
        logger.setLevel(logging.WARNING)
    elif verbose == 2:
        logger.setLevel(logging.INFO)
    elif verbose > 2:
        logger.setLevel(logging.DEBUG)

    with open(config, "r") as fp, UBXStream(port) as ubx:
        for i, line in enumerate(fp):
            cmd = bytes.fromhex(line.strip())

            ubx.write(cmd)

            try:
                reply = ubx.read()
            except Exception as e:
                if warn_only:
                    logger.warn(f"Exception during reading: {str(e)}")
                    reply = None
                else:
                    raise

            if reply is not None:
                logger.info(f"response: {reply}")
            else:
                logger.info("No reply from device")

            time.sleep(0.1)


if __name__ == "__main__":
    write_config()
