# Serial Port Debugging Software

![](./main.jpg)

## Install and run
    install by pip
        pip install PortDebug
    run
        PortDebug

This is a software for serial debugging that supports the following features:

- Serial data logging
- JavaScript script support

## Features

- **Serial Data Logging**: Records serial communication data for later analysis.
- **JavaScript Script Support**: Allows automation of serial operations and data processing through JavaScript scripts.

A demo for caculate crc16 modbus

CalcArr : "5A 1B CD"

return : "5A 1B CD 45 23"

    function processData(CalcArr) {
        var arr = CalcArr.split(" "), crc = 0xFFFF, polynomial = 0xA001;
        for (var i = 0; i < arr.length; i++) {
            crc ^= parseInt(arr[i], 16);
            for (var j = 0; j < 8; j++) crc = (crc & 0x0001) ? (crc >> 1) ^ polynomial : crc >> 1;
        }
        arr.push(((crc >> 8) & 0xFF).toString(16).toUpperCase(), (crc & 0xFF).toString(16).toUpperCase());
        return arr;
    }
