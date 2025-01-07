# Serial Port Debugging Software

![](./main.jpg)

This is a software for serial debugging that supports the following features:

- Serial data logging
- JavaScript script support

## Features

- **Serial Data Logging**: Records serial communication data for later analysis.
- **JavaScript Script Support**: Allows automation of serial operations and data processing through JavaScript scripts.

A demo for caculate crc16
CalcArr : "5A 1B CD"
return : "5A 1B CD"

function processData(CalcArr) {
    var arr = CalcArr.split(" ");
    var crc = 0xFFFF; // Initial CRC value
    var polynomial = 0xA001; // Polynomial used for CRC-16


    // Calculate CRC-16
    for (var i = 0; i < arr.length; i++) {
        crc ^= parseInt(arr[i], 16); // XOR the current byte with the CRC
        for (var j = 0; j < 8; j++) {
            if (crc & 0x0001) { // If the lowest bit is set
                crc = (crc >> 1) ^ polynomial; // Shift right and XOR with polynomial
            } else {
                crc >>= 1; // Just shift right
            }
        }
    }


    // Get the two bytes of the CRC-16 result
    var crcHigh = (crc >> 8) & 0xFF; // High byte
    var crcLow = crc & 0xFF; // Low byte


    // Append the CRC-16 result as separate hexadecimal values
    arr.push(crcHigh.toString(16).toUpperCase()); // High byte
    arr.push(crcLow.toString(16).toUpperCase()); // Low byte


    return arr;  
}

