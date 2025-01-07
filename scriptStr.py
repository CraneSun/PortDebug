non_parity = '''
    function processData(CalcArr) {
        var arr = CalcArr.split(" ");
        return arr;  
    }
    '''
crc8_parity = '''
//autosar
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
    '''

crc16_parity = '''
//modbus
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
    '''

crc32_parity = '''
//iso-hdlc
function processData(CalcArr) {
    var arr = CalcArr.split(" ");
    var crc = 0xFFFFFFFF; // Initial CRC value
    var polynomial = 0xEDB88320; // Polynomial used for CRC-32

    // Create a CRC-32 table
    var crcTable = new Uint32Array(256);
    for (var i = 0; i < 256; i++) {
        var temp = i;
        for (var j = 0; j < 8; j++) {
            temp = (temp >>> 1) ^ (polynomial & ~((temp & 1) - 1));
        }
        crcTable[i] = temp >>> 0; // Store the CRC value in the table
    }

    // Calculate CRC-32
    for (var i = 0; i < arr.length; i++) {
        crc = (crc >>> 8) ^ crcTable[(crc ^ parseInt(arr[i], 16)) & 0xFF]; // Update CRC using the table
    }

    // Final CRC value
    crc ^= 0xFFFFFFFF;

    // Get the four bytes of the CRC-32 result
    var crcByte1 = (crc >> 24) & 0xFF; // First byte (highest)
    var crcByte2 = (crc >> 16) & 0xFF; // Second byte
    var crcByte3 = (crc >> 8) & 0xFF;  // Third byte
    var crcByte4 = crc & 0xFF;         // Fourth byte (lowest)

    // Append the CRC-32 result as separate hexadecimal values
    arr.push(crcByte1.toString(16).toUpperCase()); // First byte
    arr.push(crcByte2.toString(16).toUpperCase()); // Second byte
    arr.push(crcByte3.toString(16).toUpperCase()); // Third byte
    arr.push(crcByte4.toString(16).toUpperCase()); // Fourth byte

    return arr;  
}

    '''

sum_parity = '''
function processData(CalcArr) {
    var arr = CalcArr.split(" ");
    var sum = 0;
    for (var i = 0; i < arr.length; i++) {
        sum += parseInt(arr[i], 16); 
    }
    sum = sum & 0xff;
    arr.push(sum.toString(16).toUpperCase()); 
    return arr;  
}
    '''