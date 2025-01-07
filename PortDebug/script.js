function processData(CalcArr) {
    var arr = CalcArr.split(" ");
    var crc = 0xFF; // Initial CRC value for AUTOSAR
    var polynomial = 0x2F; // Polynomial used for AUTOSAR CRC-8


    // Calculate AUTOSAR CRC-8
    for (var i = 0; i < arr.length; i++) {
        // Convert each hex string to a number
        var byte = parseInt(arr[i], 16);
        crc ^= byte; // XOR the current byte with the CRC
        for (var j = 0; j < 8; j++) {
            if (crc & 0x80) { // If the highest bit is set
                crc = (crc << 1) ^ polynomial; // Shift left and XOR with polynomial
            } else {
                crc <<= 1; // Just shift left
            }
            crc &= 0xFF; // Keep CRC within 8 bits
        }
    }

crc ^= 0xFF;
    // Append the AUTOSAR CRC-8 result as a hexadecimal value
    arr.push(crc.toString(16).toUpperCase()); 


    return arr;  
}