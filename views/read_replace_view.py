from PyQt5.QtWidgets import QTableWidget, QHBoxLayout, QPushButton, QTableWidgetItem, QDialog, QVBoxLayout


class ReadReplaceDialog(QDialog):
    """Dialog to configure read/replace key-value pairs."""
    def __init__(self, initial_data=None):
        super().__init__()
        self.setWindowTitle("Read and Replace Settings")
        self.setMinimumSize(400, 300)
        layout = QVBoxLayout()

        # Table setup
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Read", "Replace"])
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 200)
        if initial_data:
            self.populate_table(initial_data)
        layout.addWidget(self.table)

        # Add/Remove buttons
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add Row")
        add_btn.clicked.connect(self.add_row)
        remove_btn = QPushButton("Remove Row")
        remove_btn.clicked.connect(self.remove_row)
        button_layout.addWidget(add_btn)
        button_layout.addWidget(remove_btn)
        layout.addLayout(button_layout)

        # Save/Cancel buttons
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def add_row(self):
        self.table.insertRow(self.table.rowCount())

    def remove_row(self):
        selected = self.table.selectionModel().selectedRows()
        for row in reversed(selected):
            self.table.removeRow(row.row())

    def populate_table(self, data):
        self.table.setRowCount(len(data))
        for row, (read, replace) in enumerate(data.items()):
            self.table.setItem(row, 0, QTableWidgetItem(read))
            self.table.setItem(row, 1, QTableWidgetItem(replace))

    def get_data(self):
        data = {}
        for row in range(self.table.rowCount()):
            read_item = self.table.item(row, 0)
            replace_item = self.table.item(row, 1)
            if read_item and (read_text := read_item.text().strip()):
                replace_text = replace_item.text().strip() if replace_item else ""
                data[read_text] = replace_text
        return data