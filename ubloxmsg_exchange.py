#!/usr/bin/python
#
# ubx packet exchange
#
# v0.5
#
# Wilfried Klaebe <wk-openmoko@chaos.in-kiel.de>
# Justus Paulick <justus.paulick@tu-dresden.de>
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


TIMEOUT = 5  # s


def get_binary(input):
    cs0 = 0
    cs1 = 0
    ret = "\xb5\x62"

    for d in input:
        c = binascii.unhexlify(d)
        ret += c
        cs0 += ord(c)
        cs0 &= 255
        cs1 += cs0
        cs1 &= 255

    ret += chr(cs0)+chr(cs1)
    return ret


with open(sys.argv[1]) as fp:
    with serial.Serial(sys.argv[2], 9600, timeout=TIMEOUT) as radio:
        line = fp.readline()
        cnt = 1
        recv = bytearray()

        while line:
            line = re.findall(
                r"([A-F][0-9]|[A-F][A-F]|[0-9][A-F]|[0-9][0-9])\s", line)

            print("config-line: " + str(line) + " count: " + str(cnt))
            msg = get_binary(line)
            radio.write(bytearray(msg))

            ubx_msg = False
            time_start = time.time()

            while ubx_msg == False:
                recv = radio.read(1)
                if recv[0] == '\xb5':  # muh - start UBX Message
                    recv += radio.read(1)

                    if recv[1] == '\x62':  # b
                        ubx_msg = True
                        break

                if time.time() > time_start + TIMEOUT:
                    break

            if ubx_msg:
                recv += radio.read(2)  # header
                recv += radio.read(1)  # length
                length = ord(recv[4])
                recv += radio.read(length+2)  # payload + read checksum

                s = ""
                for i in recv:
                    s += binascii.hexlify(i)
                    s += " "

                print("response: " + s)
            else:
                print("no response was received in timeout")

            time.sleep(1)
            line = fp.readline()
            cnt += 1

        radio.close()
