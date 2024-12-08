from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, QHeaderView
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from utils.helpers import load_mapping_from_json, resource_path


class ViewportView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        # Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Tag Name", "Tag Value", "Assignment", "Static Attribute Value"])
        layout.addWidget(self.table)

        # Make columns split evenly
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        self.setLayout(layout)

        # Predefined options for the dropdown
        self.assignment_options = self.generate_assignment_options()

        # Load tag-to-assignment mappings from the JSON5 file
        self.tag_to_assignment = self.load_tag_to_assignment_file()

    def populate_table(self, data):
        """Populates the table with data and auto-assigns values where applicable."""
        self.table.setRowCount(len(data))
        for row, item in enumerate(data):
            tag = item.get("Tag", "")
            value = item.get("Value", "")

            # Set Tag Name
            self.table.setItem(row, 0, QTableWidgetItem(tag))

            # Set Tag Value
            self.table.setItem(row, 1, QTableWidgetItem(value))

            # Set Assignment dropdown
            combo = QComboBox()
            combo.addItems(self.assignment_options)

            # Auto-assign based on the tag-to-assignment mapping
            if tag in self.tag_to_assignment:
                assignment = self.tag_to_assignment[tag]
                combo.setCurrentText(assignment)
            else:
                assignment = "VARIABLE"
                combo.setCurrentText(assignment)

            # Connect dropdown signal for dynamic row highlighting
            combo.currentTextChanged.connect(lambda text, r=row: self.highlight_row_if_static(r, text))
            self.table.setCellWidget(row, 2, combo)  # Add combo box to "Assignment" column

    def load_tag_to_assignment_file(self):
        """Load tag-to-assignment mappings from a JSON5 file."""
        filepath = resource_path("Dict/AttributeDictionary.json5")
        try:
            return load_mapping_from_json(filepath)
        except (FileNotFoundError, ValueError) as e:
            print(f"Error loading tag-to-assignment mapping: {str(e)}")
            return {}  # Fallback to an empty mapping

    @staticmethod
    def generate_assignment_options():
        """Generate the list of assignment options."""
        base_options = [
            "REVISION", "VARIABLE", "STATIC", "DWG No.",
            "DWG TITLE 1", "DWG TITLE 2", "DWG TITLE 3", "DWG TITLE 4"
        ]

        # Generate revision options up to 10
        for i in range(1, 11):  # From REV 1 to REV 10
            base_options.extend([
                f"REV {i} REV", f"REV {i} DATE", f"REV {i} DESC", f"REV {i} DESIGNER",
                f"REV {i} DRAFTED", f"REV {i} CHECKED", f"REV {i} RPEQ",
                f"REV {i} RPEQSIGN", f"REV {i} COMPANY"
            ])

        return base_options

    def highlight_row_if_static(self, row, text):
        """
        Highlight the entire row yellow if "STATIC" is selected in the dropdown.
        """
        if text == "STATIC":
            color = QColor(Qt.yellow)
        else:
            color = QColor(Qt.white)

        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if not item:
                item = QTableWidgetItem("")  # Create an empty item if none exists
                self.table.setItem(row, col, item)
            item.setBackground(color)

    def extract_static_fields(self):
        """
        Extract fields marked as STATIC from the table.

        Returns:
        - A list of dictionaries, each containing a "Tag" and its "Value".
        """
        static_fields = []

        for row in range(self.table.rowCount()):
            assignment = self.table.cellWidget(row, 2).currentText()  # Assignment dropdown
            if assignment == "STATIC":
                tag = self.table.item(row, 0).text()  # Tag Name
                value = self.table.item(row, 3).text()  # Static Attribute Value
                if tag and value:
                    static_fields.append({"Tag": tag, "Value": value})

        return static_fields

    def extract_all_table_data(self):
        """
        Extract all data from the table.

        Returns:
        - A list of dictionaries, each representing a row with keys:
          - "Tag", "Value", "Assignment", and "Static Value".
        """
        table_data = []
        for row in range(self.table.rowCount()):
            tag = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
            value = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
            assignment = self.table.cellWidget(row, 2).currentText() if self.table.cellWidget(row, 2) else ""
            static_value = self.table.item(row, 3).text() if self.table.item(row, 3) else ""
            table_data.append({
                "Tag": tag,
                "Value": value,
                "Assignment": assignment,
                "StaticValue": static_value
            })
        return table_data
