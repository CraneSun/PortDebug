'''
author: sunkun
date: 2025-01-05
generate by claude-3.5-sonnet
write by python
license: MIT
copyright: 2025 sunkun

'''
import sys, json
from py_mini_racer import py_mini_racer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,QFileDialog, 
    QComboBox, QPushButton, QLineEdit, QFormLayout, QTextEdit, QTableWidget, 
    QTableWidgetItem, QCheckBox, QDialog, QHeaderView, QSplitter, QSpinBox, 
    QMessageBox, QDockWidget
)
from PySide6.QtCore import Qt, QTimer, QDateTime, QDate
from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor, QAction
import serial.tools.list_ports

non_parity = '''
    function processData(CalcArr) {
        var arr = CalcArr.split(" ");
        return arr;  
    }
    '''
crc8_parity = '''
function processData(CalcArr) {
    var arr = CalcArr.split(" "), crc = 0xFF, polynomial = 0x2F;
    for (var i = 0; i < arr.length; i++) {
        var byte = parseInt(arr[i], 16);
        crc ^= byte;
        for (var j = 0; j < 8; j++) crc = (crc & 0x80) ? (crc << 1) ^ polynomial : crc << 1, crc &= 0xFF;
    }
    arr.push((crc ^ 0xFF).toString(16).toUpperCase());
    return arr;
}
'''

crc16_parity = '''
function processData(CalcArr) {
    var arr = CalcArr.split(" "), crc = 0xFFFF, polynomial = 0xA001;
    for (var i = 0; i < arr.length; i++) {
        crc ^= parseInt(arr[i], 16);
        for (var j = 0; j < 8; j++) crc = (crc & 0x0001) ? (crc >> 1) ^ polynomial : crc >> 1;
    }
    arr.push(((crc >> 8) & 0xFF).toString(16).toUpperCase(), (crc & 0xFF).toString(16).toUpperCase());
    return arr;
}
'''

crc32_parity = '''
function processData(CalcArr) {
    var arr = CalcArr.split(" "), crc = 0xFFFFFFFF, polynomial = 0xEDB88320, crcTable = new Uint32Array(256);
    for (var i = 0; i < 256; i++) {
        var temp = i;
        for (var j = 0; j < 8; j++) temp = (temp >>> 1) ^ (polynomial & ~((temp & 1) - 1));
        crcTable[i] = temp >>> 0;
    }
    for (var i = 0; i < arr.length; i++) crc = (crc >>> 8) ^ crcTable[(crc ^ parseInt(arr[i], 16)) & 0xFF];
    crc ^= 0xFFFFFFFF;
    arr.push(((crc >> 24) & 0xFF).toString(16).toUpperCase(), ((crc >> 16) & 0xFF).toString(16).toUpperCase(), ((crc >> 8) & 0xFF).toString(16).toUpperCase(), (crc & 0xFF).toString(16).toUpperCase());
    return arr;
}
'''

sum_parity = '''
function processData(CalcArr) {
    var arr = CalcArr.split(" "), sum = 0;
    for (var i = 0; i < arr.length; i++) sum += parseInt(arr[i], 16);
    arr.push((sum & 0xFF).toString(16).toUpperCase());
    return arr;
}
'''


class RenameDialog(QDialog):
    def __init__(self, current_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rename Button")
        self.setModal(True)

        layout = QFormLayout(self)
        layout.addRow(QLabel("Enter new name:"))
        self.line_edit = QLineEdit(current_name)
        layout.addRow(self.line_edit)
        button_box = QPushButton("OK")
        button_box.clicked.connect(self.accept)
        layout.addRow(button_box)

    def get_new_name(self):
        return self.line_edit.text()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PortDebug V1.0.7")
        self.resize(1200, 800)
        self.Encode = 'utf-8'
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        left_panel = QTabWidget()
        left_panel.setFixedWidth(200)
        main_layout.addWidget(left_panel)
        
        serial_widget = QWidget()
        serial_layout = QFormLayout(serial_widget)

        self.last_ports = []
        self.port_combo = QComboBox()
        serial_layout.addRow("PORT:", self.port_combo)
        
        self.baud_combo = QComboBox()
        standard_baudrates = [
            '300', '600', '1200', '2400', '4800', '9600', '14400',
            '19200', '28800', '38400', '57600', '115200', '230400',
            '460800', '921600', '1000000', '1500000', '2000000' 
        ]
        self.baud_combo.addItems(standard_baudrates)
        self.baud_combo.setCurrentText('9600') 
        serial_layout.addRow("Baud:", self.baud_combo)

        self.data_bits_combo = QComboBox()
        self.data_bits_combo.addItems(['5', '6', '7', '8'])
        self.data_bits_combo.setCurrentText('8')
        serial_layout.addRow("Data:", self.data_bits_combo)

        self.parity_combo = QComboBox()
        self.parity_combo.addItems(['NONE', 'ODD', 'EVEN', 'MARK', 'SPACE'])
        self.parity_combo.setCurrentText('NONE')
        serial_layout.addRow("Parity:", self.parity_combo)

        self.stop_bits_combo = QComboBox()
        self.stop_bits_combo.addItems(['1', '1.5', '2'])
        self.stop_bits_combo.setCurrentText('1')
        serial_layout.addRow("Stop:", self.stop_bits_combo)

        self.flow_control_combo = QComboBox()
        self.flow_control_combo.addItems(['OFF', 'RTS/CTS', 'XON/XOFF'])
        self.flow_control_combo.setCurrentText('OFF')
        serial_layout.addRow("Flow:", self.flow_control_combo)


        self.serial_port = None
        self.open_button = QPushButton("Open")
        self.open_button.clicked.connect(self.toggle_port)
        serial_layout.addWidget(self.open_button)
        left_panel.addTab(serial_widget, "Serial")
        
        tcp_widget = QWidget()
        tcp_layout = QFormLayout(tcp_widget)
        tcp_layout.addRow("IP:", QLineEdit())
        tcp_layout.addRow("Port:", QLineEdit())
        tcp_layout.addWidget(QPushButton("Connect"))
        #left_panel.addTab(tcp_widget, "TCP/IP")
        
        udp_widget = QWidget()
        udp_layout = QFormLayout(udp_widget)
        udp_layout.addRow("LocalPort:", QLineEdit())
        udp_layout.addRow("Dest IP:", QLineEdit())
        udp_layout.addRow("Dest Port:", QLineEdit())
        udp_layout.addWidget(QPushButton("bind"))
        #left_panel.addTab(udp_widget, "UDP")
        
        
        middle_panel = QWidget()
        middle_layout = QVBoxLayout(middle_panel)
        main_layout.addWidget(middle_panel)
        
        self.receive_area = QTextEdit()
        self.receive_area.setReadOnly(True)
        
        send_group = QWidget()
        send_layout = QVBoxLayout(send_group)
        self.send_area = QTextEdit()
        self.send_area.setMaximumHeight(100)
        
        send_control_layout = QHBoxLayout()
        self.hex_recv_cb = QCheckBox("HEX Recv")
        self.hex_send_cb = QCheckBox("HEX Send")
        script_edit_btn = QPushButton("JSScript")
        self.send_btn = QPushButton("Send")
        clear_send_btn = QPushButton("Clear")
        self.send_btn.clicked.connect(lambda:self.send_data(self.send_area.toPlainText().strip(), self.hex_send_cb.isChecked()))

        self.checksum_combo = QComboBox()
        self.checksum_combo.addItems(["NONE", "JSScript", "CRC8", "CRC16", "CRC32", "SUM"])
        self.checksum_combo.setCurrentText("NONE")
        self.ctx = py_mini_racer.MiniRacer()
        self.script_content = self.get_srcipt_content()
        self.ctx.eval(self.script_content)
        self.checksum_combo.currentIndexChanged.connect(self.update_script_content) 

        send_control_layout.addWidget(self.hex_recv_cb)
        send_control_layout.addWidget(self.hex_send_cb)
        send_control_layout.addWidget(script_edit_btn)
        send_control_layout.addWidget(self.checksum_combo)
        send_control_layout.addStretch()
        send_control_layout.addWidget(clear_send_btn)
        send_control_layout.addWidget(self.send_btn)
        script_edit_btn.clicked.connect(self.edit_script)

        # send_layout.addWidget(send_label)
        send_layout.addWidget(self.send_area)
        send_layout.addLayout(send_control_layout)
        
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.receive_area)
        splitter.addWidget(send_group)
        middle_layout.addWidget(splitter)
        
        splitter.setStretchFactor(0, 7)  
        splitter.setStretchFactor(1, 3)  
        
        self.right_panel = QDockWidget("Command list", self)
        self.right_panel.setAllowedAreas(Qt.RightDockWidgetArea) 

        right_content = QWidget()
        right_layout = QVBoxLayout(right_content)

        self.command_table = QTableWidget(100, 4)  
        self.command_table.setHorizontalHeaderLabels(["hex", "command", "send", "loop"])

        self.command_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.command_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.command_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.command_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.command_table.setColumnWidth(0, 30)
        self.command_table.setColumnWidth(2, 60)
        self.command_table.setColumnWidth(3, 60)

        for i in range(100):
            hex_cb = QCheckBox()
            self.command_table.setCellWidget(i, 0, hex_cb)
            self.command_table.setItem(i, 1, QTableWidgetItem(""))

            send_button = QPushButton("Send")
            send_button.clicked.connect(lambda checked, r=i: self.handle_send_button_click(r))
            send_button.setContextMenuPolicy(Qt.CustomContextMenu)
            send_button.customContextMenuRequested.connect(lambda pos, btn=send_button, : self.handle_button_rename(btn))
            self.command_table.setCellWidget(i, 2, send_button)

            cycle_spin = QSpinBox()
            cycle_spin.setRange(0, 100)
            cycle_spin.setToolTip("0:No Loop 1-3:Loop")
            self.command_table.setCellWidget(i, 3, cycle_spin)

        right_layout.addWidget(self.command_table)
        self.right_panel.setWidget(right_content)
        #self.right_panel.resize(800, self.right_panel.height())

        self.addDockWidget(Qt.RightDockWidgetArea, self.right_panel)

        toggle_dock_action = QAction("Commands", self)
        toggle_dock_action.triggered.connect(self.toggle_dock_widget)
        self.menuBar().addAction(toggle_dock_action)

        save_log = QAction("SaveLog", self)
        save_log.triggered.connect(self.save_receive_log)
        self.menuBar().addAction(save_log)

        main_layout.setStretch(1, 1)  

        self.scan_ports()
        self.port_timer = QTimer()
        self.port_timer.timeout.connect(self.scan_ports)
        self.port_timer.start(1000)  

        self.receive_timer = QTimer()
        self.receive_timer.timeout.connect(self.read_data)

        self.load_from_json()

    def save_receive_log(self):
        default_filename = f"PortDebug_log_{QDateTime.currentDateTime().toString('yyyyMMdd_HHmm')}.txt"
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Log", default_filename, "Log Files (*.txt);;All Files (*)", options=options)
        if file_path:
            with open(file_path, "w") as f:
                f.write(self.receive_area.toPlainText())

    def toggle_dock_widget(self):
        if self.right_panel.isVisible():
            self.right_panel.hide()
        else:
            self.right_panel.show()


    def scan_ports(self):
        current_ports = [port.device for port in serial.tools.list_ports.comports()]
        if current_ports == self.last_ports:
            return
        current_selection = self.port_combo.currentText()
        self.port_combo.clear()
        self.port_combo.addItems(current_ports)
        if current_selection in current_ports:
            self.port_combo.setCurrentText(current_selection)
        self.last_ports = current_ports
    
    def enable_port(self):
        self.port_combo.setEnabled(False)
        self.baud_combo.setEnabled(False)
        self.parity_combo.setEnabled(False)
        self.data_bits_combo.setEnabled(False)
        self.stop_bits_combo.setEnabled(False)
        self.flow_control_combo.setEnabled(False)
        self.open_button.setText("Close")
        self.receive_timer.start(16)  

    def disable_port(self):
        self.port_combo.setEnabled(True)
        self.baud_combo.setEnabled(True)
        self.data_bits_combo.setEnabled(True)
        self.parity_combo.setEnabled(True)
        self.stop_bits_combo.setEnabled(True)
        self.flow_control_combo.setEnabled(True)
        self.open_button.setText("Open")
        self.receive_timer.stop()

    def toggle_port(self):
        if self.serial_port is None:
            try:
                self.serial_port = serial.Serial(
                    port=self.port_combo.currentText(),
                    baudrate=int(self.baud_combo.currentText())
                )
                self.enable_port()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Serial Port open failed: {str(e)}")
        else:
            self.serial_port.close()
            self.serial_port = None
            self.disable_port()


    def read_data(self):
        if self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting:
                    data = self.serial_port.read_all()
                    if data:
                        if self.receive_area.document().characterCount() > 2000000:
                            cursor = self.receive_area.textCursor()
                            cursor.movePosition(QTextCursor.Start)
                            cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
                            text = cursor.selectedText()
                            half_length = len(text) // 2
                            cursor.removeSelectedText()
                            cursor.insertText(text[half_length:])
                        current_time = QDateTime.currentDateTime()
                        time_str = current_time.toString('->[hh:mm:ss.zzz]: ')
                        
                        background = self.receive_area.palette().color(self.receive_area.backgroundRole())
                        is_dark = background.lightness() < 128
                        text_color = QColor("#00FF00") if is_dark else QColor("#008000") 
                        text_format = QTextCharFormat()
                        text_format.setForeground(text_color)
                        cursor = self.receive_area.textCursor()
                        cursor.movePosition(QTextCursor.End)
                        
                        if self.hex_recv_cb.isChecked():
                            hex_str = ' '.join([f'{b:02X}' for b in data])
                            cursor.insertText(time_str + f"[HEX] {hex_str}\n", text_format)
                        else:
                            try:
                                text = data.decode('utf-8')
                                cursor.insertText(time_str + text + '\n', text_format)
                            except UnicodeDecodeError:
                                hex_str = ' '.join([f'{b:02X}' for b in data])
                                cursor.insertText(time_str + f"[HEX] {hex_str}\n", text_format)
                        
                        self.receive_area.setTextCursor(cursor)
                        
            except Exception as e:
                QMessageBox.critical(self, "Error", f"failed to read data: {str(e)}")
                try:
                    self.serial_port.close()
                except:
                    pass
                self.serial_port = None
                self.disable_port()

    def update_script_content(self):
        self.script_content = self.get_srcipt_content()
        self.ctx.eval(self.script_content)

    def get_srcipt_content(self):
        selected_script = self.checksum_combo.currentText()
        script_content = ""

        if selected_script == "NONE":
            return non_parity
        elif selected_script == "JSScript":
            script_file = "script.js"
            try:
                with open(script_file, 'r') as f:
                    script_content = f.read()
                return script_content
            except FileNotFoundError:
                QMessageBox.warning(self, "Warning", "Scipt is not exist！")
                return non_parity
        elif selected_script == "CRC8":
                return crc8_parity
        elif selected_script == "CRC16":
                return crc16_parity
        elif selected_script == "CRC32":
                return crc32_parity
        else:
            return sum_parity

    def send_data(self,data, is_hex):
        if not self.serial_port or not self.serial_port.is_open:
            QMessageBox.warning(self, "Warning", "Open the serial port first！")
            return
            
        try:
            if not data:
                QMessageBox.warning(self, "Warninig", "data is empty！")
                return

            current_time = QDateTime.currentDateTime().toString("hh:mm:ss.zzz")
            background = self.receive_area.palette().color(self.receive_area.backgroundRole())
            is_dark = background.lightness() < 128
            text_color = QColor("#FF8000") if is_dark else QColor("#707000") 
            text_format = QTextCharFormat()
            text_format.setForeground(text_color)
            cursor = self.receive_area.textCursor()
            cursor.movePosition(QTextCursor.End)
            if(is_hex):
                message = f"<-[{current_time}]: [HEX] {data}\n"
            else:
                message = f"<-[{current_time}]: {data}\n"

            cursor.insertText(message,text_format)
            self.receive_area.setTextCursor(cursor)

            if is_hex:
                data = data.replace(" ","")
                if all(c in '0123456789ABCDEF' for c in data.upper()):
                    input_data = ' '.join(data[i:i+2] for i in range(0, len(data), 2))
                else:
                    QMessageBox.warning(self, "Warning", "data is not hex format！ ")
                    return;
            else:
                input_data = ' '.join(format(byte, '02X') for byte in data.encode(self.Encode))

            hex_list = self.ctx.call("processData", input_data)

            if is_hex:
                result_array = bytes(int(h.zfill(2), 16) for h in hex_list)
            else:
                result_array = bytes(int(h, 16) for h in hex_list) 

            if is_hex:
                self.serial_port.write(result_array)
            else:
                self.serial_port.write(result_array)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"failed to send data: {str(e)}")


    def edit_script(self):
        script_file = "script.js"
        try:
            with open(script_file, 'r') as f:
                script_content = f.read()
        except FileNotFoundError:
            script_content = ""  

        script_editor = QDialog(self)
        script_editor.setWindowTitle("script edit")
        script_editor.setFixedSize(600, 400)

        layout = QVBoxLayout(script_editor)

        script_text_edit = QTextEdit()
        script_text_edit.setPlainText(script_content)
        layout.addWidget(script_text_edit)

        save_button = QPushButton("save script")
        layout.addWidget(save_button)

        def save_script():
            with open(script_file, 'w') as f:
                f.write(script_text_edit.toPlainText())
            script_editor.accept() 
            self.ctx.eval(script_text_edit.toPlainText().strip())

        save_button.clicked.connect(save_script)
        script_editor.exec()

    def handle_send_button_click(self, row):
        command_content = self.command_table.item(row, 1).text()  # Assuming the command is in the second column
        isHex = self.command_table.cellWidget(row, 0).isChecked()  # Assuming the command is in the second column
        self.send_data(command_content,isHex) 

    def handle_button_rename(self, button):
        # Show a dialog to rename the button
        dialog = RenameDialog(button.text(), self)
        if dialog.exec() == QDialog.Accepted:
            new_name = dialog.get_new_name()
            button.setText(new_name)
            button.repaint()
            self.command_table.repaint()

    def closeEvent(self, event):
        self.save_to_json()
        event.accept() 

    def load_from_json(self):
        try:
            with open("config.json", "r") as json_file:
                data = json.load(json_file)

            # Load the content of the send area
            self.send_area.setText(data.get("send_content", ""))

            # Update the command list without reinitializing the UI
            for row in range(self.command_table.rowCount()):
                if row < len(data.get("commands", [])):
                    command = data["commands"][row]
                    # Update HEX checkbox
                    hex_cb = self.command_table.cellWidget(row, 0)
                    if hex_cb:
                        hex_cb.setChecked(command.get("hex", False))

                    command_content = command.get("command", "")
                    self.command_table.item(row, 1).setText(command_content)

                    btn_name = command.get("btn_name", "Send")
                    btn = self.command_table.cellWidget(row, 2)
                    btn.setText(btn_name)

                    # Update loop value
                    cycle_value = command.get("cycle", 0)
                    cycle_spin = self.command_table.cellWidget(row, 3)
                    if cycle_spin:
                        cycle_spin.setValue(cycle_value)

        except FileNotFoundError:
            QMessageBox.warning(self, "A script demo", sum_parity)
        except json.JSONDecodeError:
            #self.command_table.item(0, 1).setText("Kun Sun in huzhen lishui")
            #self.command_table.item(1, 1).setText("sk602015817@hotmail.com")
            #self.command_table.item(2, 1).setText("thanks for usage")
            QMessageBox.warning(self, "A script demo", sum_parity)

    def save_to_json(self):
        data = {
            "commands": [],
            "send_content": self.send_area.toPlainText().strip()  
        }

        for row in range(self.command_table.rowCount()):
            hex_checked = self.command_table.cellWidget(row, 0).isChecked()
            command_content = self.command_table.item(row, 1).text()
            btn_name = self.command_table.cellWidget(row, 2).text()
            cycle_value = self.command_table.cellWidget(row, 3).value()

            data["commands"].append({
                "hex": hex_checked,
                "command": command_content,
                "btn_name" : btn_name,
                "cycle": cycle_value
            })

        with open("config.json", "w") as json_file:
            json.dump(data, json_file, indent=4)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

