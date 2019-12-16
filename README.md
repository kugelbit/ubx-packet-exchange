# ubx-packet-exchange

[![Build Status](https://travis-ci.com/geissdoerfer/ubx-packet-exchange.svg?branch=master)](https://travis-ci.com/geissdoerfer/ubx-packet-exchange)

Programm for sending config-messages to a ublox-receiver via serial port and display the answer.

## Usage:


```
Usage: ubx-serial [OPTIONS]

  Writes binary config file [CONFIG] to ublox device at [PORT].

Options:
  -p, --port PATH    Serial port of device  [required]
  -c, --config PATH  Binary config to send to device  [required]
  -w, --warn-only    Warn only on read errors
  -v, --verbose
  --help             Show this message and exit.
```

 - message file will be read line by line (every line should be a UBX-Message)
 - message files could be u-center-configuration files or files like the example files (see config dir)
 - the message will be sent to the UBX receiver and the program waits for an answer
 - if an UBX-Message is recieved from the UBX receiver as answer the Message will be printed in Bytes
 - if there is no answer in timeout the programm will print an information and go to the next line

 - prepends 0xb5 0x62 header and appends checksum to every Message (Line)
 - outputs first answer from ublox-reciver in bytes


## Authors:
 - Wilfried Klaebe <wk-openmoko|at|chaos.in-kiel.de>
 - Justus Paulick <justus.paulick|at|tu-dresden.de>
 - Kai Geissdoerfer <kai.geissdoerfer|at|tu-dresden.de>
