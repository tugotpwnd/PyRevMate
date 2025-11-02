# views/left_menu_view.py
from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QRadioButton, QCheckBox, QComboBox, QLineEdit, QLabel,
    QFormLayout, QProgressBar, QSpacerItem, QSizePolicy, QTextEdit, QPushButton,
    QDialog, QListWidget, QHBoxLayout, QTableWidgetItem, QTableWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
import sys
from views.summary_view import SummaryView
from views.read_replace_view import ReadReplaceDialog

class SkippedFilesDialog(QDialog):
    cleared_signal = pyqtSignal()
    def __init__(self, skipped_files_with_errors):
        super().__init__()
        self.setWindowTitle("Skipped Files")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout()
        self.table = QTableWidget(len(skipped_files_with_errors), 2)
        self.table.setHorizontalHeaderLabels(["File", "Error"])
        self.table.setColumnWidth(0, 250)
        self.table.setColumnWidth(1, 400)

        for row, (filename, error) in enumerate(skipped_files_with_errors):
            self.table.setItem(row, 0, QTableWidgetItem(filename))
            self.table.setItem(row, 1, QTableWidgetItem(error))

        layout.addWidget(self.table)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear)
        layout.addWidget(clear_button)

        self.setLayout(layout)

    def clear(self):
        self.table.clearContents()
        self.table.setRowCount(0)
        self.cleared_signal.emit()

class LeftMenuView(QGroupBox):
    # New: signal to open map dialog (controller will handle)
    map_fields_signal = pyqtSignal()

    def __init__(self, drawing_summary_manager):
        super().__init__("Settings")
        self.skipped_files_with_errors = []
        self.run_model = None
        self.drawing_summary_manager = drawing_summary_manager

        layout = QVBoxLayout()

        self.purge_checkbox = QCheckBox("Purge All")
        self.transmit_checkbox = QCheckBox("E-Transmit")
        self.increment_revision_checkbox = QCheckBox("Increment Revision")
        self.zoom_extents_checkbox = QCheckBox("Zoom Extents")
        self.read_replace_checkbox = QCheckBox("Enable Read and Replace")
        self.rename_sheets_checkbox = QCheckBox("Rename Sheets (Remove Leading Zeroes) WIP")
        self.rename_sheets_checkbox.setEnabled(False)
        self.plot_to_pdf_checkbox = QCheckBox("Plot to PDF")

        # Create text field (initially disabled)
        self.plot_style_text_box = QLineEdit()
        self.plot_style_text_box.setPlaceholderText("Enter plot style...")
        self.plot_style_text_box.setEnabled(False)

        for checkbox in [self.purge_checkbox, self.transmit_checkbox, self.increment_revision_checkbox,
                         self.zoom_extents_checkbox, self.read_replace_checkbox, self.rename_sheets_checkbox,
                         self.plot_to_pdf_checkbox]:
            layout.addWidget(checkbox)

        layout.addWidget(self.plot_style_text_box)

        # Read/Replace config
        self.read_replace_btn = QPushButton("Configure Read/Replace Pairs")
        self.read_replace_btn.clicked.connect(self.configure_read_replace)
        layout.addWidget(self.read_replace_btn)

        self.read_replace_data = {}

        # Revision form
        self.dropdown = QComboBox()
        self.dropdown.addItems(["Numerical", "Alphabetical", "Alphanumeric", "Hardset Revision"])
        self.dropdown.setEnabled(False)
        layout.addWidget(QLabel("Revision Type"))
        layout.addWidget(self.dropdown)

        self.hardset_input = QLineEdit()
        self.hardset_input.setPlaceholderText("Enter Hardset Revision")
        self.hardset_input.setEnabled(False)
        layout.addWidget(self.hardset_input)

        self.text_inputs = {}
        text_labels = ["DATE", "DESC", "DESIGNER", "DRAFTED", "CHECKED", "RPEQSIGN", "RPEQ", "COMPANY"]
        form_layout = QFormLayout()
        for label in text_labels:
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(label)
            line_edit.setEnabled(False)
            self.text_inputs[label] = line_edit
            form_layout.addRow(QLabel(label), line_edit)
        layout.addLayout(form_layout)

        # Logs
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        self.log_window.setFixedHeight(300)
        layout.addWidget(QLabel("Logs"))
        layout.addWidget(self.log_window)

        # Stop button
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.handle_stop)
        layout.addWidget(self.stop_button)

        # Skipped/Processed buttons
        skipped_layout = QHBoxLayout()
        self.skipped_button = QPushButton("Skipped Files (0)")
        self.skipped_button.setEnabled(False)
        self.skipped_button.clicked.connect(self.show_skipped_files)
        skipped_layout.addWidget(self.skipped_button)
        skipped_layout.addStretch()
        layout.addLayout(skipped_layout)

        summary_layout = QHBoxLayout()
        self.summary_button = QPushButton("Processed Files")
        self.summary_button.clicked.connect(self.show_file_summary)
        summary_layout.addWidget(self.summary_button)
        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # NEW: Map Fields button (bottom-left-ish)
        self.map_fields_button = QPushButton("Map Fields…")
        self.map_fields_button.clicked.connect(self.map_fields_signal.emit)
        layout.addWidget(self.map_fields_button)

        # Spacer + progress
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.increment_revision_checkbox.stateChanged.connect(self.toggle_increment_revision)
        self.dropdown.currentTextChanged.connect(self.toggle_hardset_input)
        self.plot_to_pdf_checkbox.stateChanged.connect(self.toggle_plot_style)

        self.setLayout(layout)
        sys.stdout = StreamRedirect(self.log_window)

    def handle_stop(self):
        if self.run_model:
            self.run_model.request_stop()
            print("Stop Requested")

    def set_run_model(self, run_model):
        self.run_model = run_model
        self.stop_button.setEnabled(True)

    def configure_read_replace(self):
        dialog = ReadReplaceDialog(self.read_replace_data)
        if dialog.exec_() == QDialog.Accepted:
            self.read_replace_data = dialog.get_data()

    def toggle_increment_revision(self, state):
        enabled = state == Qt.Checked
        self.dropdown.setEnabled(enabled)
        self.hardset_input.setEnabled(enabled and self.dropdown.currentText() == "Hardset Revision")
        for line_edit in self.text_inputs.values():
            line_edit.setEnabled(enabled)

    def toggle_plot_style(self, state):
        enabled = state == Qt.Checked
        self.plot_style_text_box.setEnabled(enabled)

    def toggle_hardset_input(self, text):
        self.hardset_input.setEnabled(text == "Hardset Revision" and self.increment_revision_checkbox.isChecked())

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def show_progress_bar(self, visible=True):
        self.progress_bar.setVisible(visible)

    def get_settings(self):
        return {
            "purge_all": self.purge_checkbox.isChecked(),
            "e_transmit": self.transmit_checkbox.isChecked(),
            "increment_revision": self.increment_revision_checkbox.isChecked(),
            "zoom_extents": self.zoom_extents_checkbox.isChecked(),
            "revision_type": self.dropdown.currentText(),
            "hardset_revision": self.hardset_input.text(),
            "attributes": {label: field.text() for label, field in self.text_inputs.items()},
            "read_replace_enabled": self.read_replace_checkbox.isChecked(),
            "read_replace_data": self.read_replace_data,
            "rename_sheets": self.rename_sheets_checkbox.isChecked(),
            "plot_to_pdf": self.plot_to_pdf_checkbox.isChecked(),
            "plot_style_table": self.plot_style_text_box.text()
        }

    def add_skipped_file(self, filename, error):
        self.skipped_files_with_errors.append((filename, error))
        self.skipped_button.setText(f"Skipped Files ({len(self.skipped_files_with_errors)})")
        self.skipped_button.setEnabled(True)

    def show_skipped_files(self):
        dialog = SkippedFilesDialog(self.skipped_files_with_errors)
        dialog.cleared_signal.connect(self.clear_skipped_files)
        dialog.exec_()

    def clear_skipped_files(self):
        self.skipped_files_with_errors.clear()
        self.skipped_button.setText("Skipped Files (0)")
        self.skipped_button.setEnabled(False)

    def show_file_summary(self):
        summary_data = self.drawing_summary_manager.generate_summary()
        summary_view = SummaryView(summary_data, self.drawing_summary_manager)
        summary_view.exec_()

class StreamRedirect:
    """Redirects stdout to a QTextEdit widget."""
    def __init__(self, text_edit):
        self.text_edit = text_edit
    def write(self, text):
        self.text_edit.append(text)
    def flush(self):
        pass
