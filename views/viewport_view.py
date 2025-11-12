# views/viewport_view.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, QHeaderView
from PyQt5.QtGui import QColor, QBrush, QPalette
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
        self._mapping_filepath = resource_path("Dict/AttributeDictionary.json5")
        self.tag_to_assignment = self.load_tag_to_assignment_file()

    # ---------- Public helpers ----------
    def get_mapping_filepath(self) -> str:
        return self._mapping_filepath

    def reload_tag_to_assignment(self):
        self.tag_to_assignment = self.load_tag_to_assignment_file()

    def refresh_row_colors(self):
        for row in range(self.table.rowCount()):
            self._apply_mapping_color(row)

    # ---------- Populate / Extract ----------
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
                idx = combo.findText(assignment)
                combo.setCurrentIndex(idx if idx >= 0 else 0)
            else:
                combo.setCurrentIndex(-1)  # show empty/unselected

            combo.currentTextChanged.connect(lambda _text, r=row: self._apply_mapping_color(r))
            self.table.setCellWidget(row, 2, combo)  # Add combo box to "Assignment" column

            # Static value cell
            if self.table.item(row, 3) is None:
                self.table.setItem(row, 3, QTableWidgetItem(""))

            # Initial color
            self._apply_mapping_color(row)

    def extract_static_fields(self):
        """
        Extract fields marked as STATIC from the table.

        Returns:
        - A list of dictionaries, each containing a "Tag" and its "Value".
        """
        static_fields = []
        for row in range(self.table.rowCount()):
            assignment = self.table.cellWidget(row, 2).currentText() if self.table.cellWidget(row, 2) else ""
            if assignment == "STATIC":
                tag = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
                value = self.table.item(row, 3).text() if self.table.item(row, 3) else ""
                if tag and value:
                    static_fields.append({"Tag": tag, "Value": value})
        return static_fields

    def extract_all_table_data(self):
        """
        Extract all data from the table.

        Returns:
        - A list of dictionaries per row: "Tag","Value","Assignment","StaticValue".
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

    # ---------- Private: mapping + coloring ----------
    def load_tag_to_assignment_file(self):
        """Load tag-to-assignment mappings from a JSON5 file."""
        try:
            return load_mapping_from_json(self._mapping_filepath)
        except Exception as e:
            print(f"Error loading tag-to-assignment mapping: {str(e)}")
            return {}  # Fallback to an empty mapping

    def _apply_mapping_color(self, row: int):
        """
        Dark/Light friendly coloring:
          - No selection  -> muted red overlay
          - Correct match -> muted green overlay
          - Otherwise     -> transparent (inherits table bg)
        Text color auto-contrasts with background.
        """
        # Detect theme roughly from base color lightness
        base = self.table.palette().color(QPalette.Base)
        is_dark = base.value() < 128

        # Decide background color for the row
        tag_item = self.table.item(row, 0)
        tag = tag_item.text().strip() if tag_item else ""

        combo = self.table.cellWidget(row, 2)
        selected = combo.currentText().strip() if combo and combo.currentIndex() >= 0 else ""

        if not selected:
            # RED
            bg = QColor(180, 70, 70, 170) if is_dark else QColor(255, 210, 210)
        else:
            mapped = self.tag_to_assignment.get(tag, "")
            if mapped and selected == mapped:
                # GREEN
                bg = QColor(60, 140, 95, 150) if is_dark else QColor(210, 255, 210)
            else:
                # No special highlight; use table background (fixes "white on white" in dark mode)
                bg = QColor(0, 0, 0, 0)

        # Compute a readable foreground for the row
        def _fg_for(c: QColor) -> QColor:
            if c.alpha() == 0:
                return QColor()  # default
            # Relative luminance-ish
            lum = 0.2126 * c.red() + 0.7152 * c.green() + 0.0722 * c.blue()
            return QColor(0, 0, 0) if lum > 150 else QColor(255, 255, 255)

        fg = _fg_for(bg)

        for col in range(self.table.columnCount()):
            cell = self.table.item(row, col)
            if cell is None:
                cell = QTableWidgetItem("")
                self.table.setItem(row, col, cell)
            cell.setBackground(bg)
            if fg.isValid():
                cell.setForeground(QBrush(fg))
            else:
                # Clear custom foreground to inherit table default
                cell.setForeground(QBrush())
    @staticmethod
    def generate_assignment_options():
        """Generate the list of assignment options."""
        base_options = [
            "REVISION", "VARIABLE", "STATIC", "DWG No.",
            "DWG TITLE 1", "DWG TITLE 2", "DWG TITLE 3", "DWG TITLE 4"
        ]
        for i in range(1, 11):  # From REV 1 to REV 10
            base_options.extend([
                f"REV {i} REV", f"REV {i} DATE", f"REV {i} DESC", f"REV {i} DESIGNER",
                f"REV {i} DRAFTED", f"REV {i} CHECKED", f"REV {i} RPEQ",
                f"REV {i} RPEQSIGN", f"REV {i} COMPANY"
            ])
        return base_options
