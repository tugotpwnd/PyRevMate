from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QRadioButton, QCheckBox, QComboBox, QLineEdit, QLabel,
    QFormLayout, QProgressBar, QSpacerItem, QSizePolicy, QTextEdit, QPushButton, QDialog, QListWidget, QHBoxLayout,
    QTableWidgetItem, QTableWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
import sys
from views.summary_view import SummaryView


class SkippedFilesDialog(QDialog):
    """A dialog to display skipped files and their errors."""
    cleared_signal = pyqtSignal()  # Signal to notify that the skipped files are cleared

    def __init__(self, skipped_files_with_errors):
        super().__init__()
        self.setWindowTitle("Skipped Files")
        self.setMinimumSize(500, 400)
        layout = QVBoxLayout()

        # Table for displaying skipped files with errors
        self.table = QTableWidget(len(skipped_files_with_errors), 2)
        self.table.setHorizontalHeaderLabels(["File", "Error"])
        self.table.setColumnWidth(0, 250)  # Adjust column widths
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
        """Clear the table and reset skipped files."""
        self.table.clearContents()  # Clears the contents of the table
        self.table.setRowCount(0)  # Resets the number of rows to 0
        self.cleared_signal.emit()  # Emit a signal to notify parent class


class LeftMenuView(QGroupBox):
    def __init__(self, drawing_summary_manager):
        super().__init__("Settings")
        self.skipped_files_with_errors = []  # To keep track of skipped files and their errors
        self.run_model = None  # Placeholder for the RunModel instance
        self.drawing_summary_manager = drawing_summary_manager

        layout = QVBoxLayout()

        # Example checkboxes
        self.purge_checkbox = QCheckBox("Purge All")
        self.transmit_checkbox = QCheckBox("E-Transmit")
        self.increment_revision_checkbox = QCheckBox("Increment Revision")
        self.zoom_extents_checkbox = QCheckBox("Zoom Extents")
        layout.addWidget(self.purge_checkbox)
        layout.addWidget(self.transmit_checkbox)
        layout.addWidget(self.increment_revision_checkbox)
        layout.addWidget(self.zoom_extents_checkbox)

        # Dropdown for Revision Type
        self.dropdown = QComboBox()
        self.dropdown.addItems(["Numerical", "Alphabetical", "Alphanumeric", "Hardset Revision"])
        self.dropdown.setEnabled(False)  # Initially disabled
        layout.addWidget(QLabel("Revision Type"))
        layout.addWidget(self.dropdown)

        # Text input for Hardset Revision (dynamically enabled)
        self.hardset_input = QLineEdit()
        self.hardset_input.setPlaceholderText("Enter Hardset Revision")
        self.hardset_input.setEnabled(False)  # Initially disabled
        layout.addWidget(self.hardset_input)

        # Text input fields for other attributes
        self.text_inputs = {}
        text_labels = [
            "DATE", "DESC", "DESIGNER", "DRAFTED",
            "CHECKED", "RPEQSIGN", "RPEQ", "COMPANY"
        ]
        form_layout = QFormLayout()
        for label in text_labels:
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(label)
            line_edit.setEnabled(False)  # Initially disabled
            self.text_inputs[label] = line_edit
            form_layout.addRow(QLabel(label), line_edit)
        layout.addLayout(form_layout)

        # Add a text window for logs
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)  # Make it read-only
        self.log_window.setFixedHeight(300)  # Set a fixed height for the log window
        layout.addWidget(QLabel("Logs"))
        layout.addWidget(self.log_window)

        # Add Stop button
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)  # Initially disabled
        self.stop_button.clicked.connect(self.handle_stop)
        layout.addWidget(self.stop_button)

        # Skipped files button
        skipped_layout = QHBoxLayout()
        self.skipped_button = QPushButton("Skipped Files (0)")
        self.skipped_button.setEnabled(False)  # Initially disabled
        self.skipped_button.clicked.connect(self.show_skipped_files)
        skipped_layout.addWidget(self.skipped_button)
        skipped_layout.addStretch()  # Push the button to the left
        layout.addLayout(skipped_layout)

        # Summary button
        summary_layout = QHBoxLayout()
        self.summary_button = QPushButton("Processed Files")
        self.summary_button.clicked.connect(self.show_file_summary)
        summary_layout.addWidget(self.summary_button)
        summary_layout.addStretch()  # Push the button to the left
        layout.addLayout(summary_layout)

        # Add a spacer to push widgets to the top
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)

        # Loading bar at the bottom
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)  # Initially empty
        self.progress_bar.setVisible(False)  # Hidden by default
        layout.addWidget(self.progress_bar)

        # Connect checkbox and dropdown signals
        self.increment_revision_checkbox.stateChanged.connect(self.toggle_increment_revision)
        self.dropdown.currentTextChanged.connect(self.toggle_hardset_input)

        self.setLayout(layout)

        # Redirect stdout to the log window
        sys.stdout = StreamRedirect(self.log_window)

    def handle_stop(self):
        """Handle stop button click."""
        if self.run_model:
            self.run_model.request_stop()
            print("Stop Requested")

    def set_run_model(self, run_model):
        """Set the RunModel instance."""
        self.run_model = run_model
        self.stop_button.setEnabled(True)  # Enable the Stop button

    def toggle_increment_revision(self, state):
        """Enable or disable the dropdown and text inputs based on checkbox state."""
        enabled = state == Qt.Checked
        self.dropdown.setEnabled(enabled)
        self.hardset_input.setEnabled(enabled and self.dropdown.currentText() == "Hardset Revision")
        for line_edit in self.text_inputs.values():
            line_edit.setEnabled(enabled)

    def toggle_hardset_input(self, text):
        """Enable or disable the Hardset Revision input based on dropdown value."""
        self.hardset_input.setEnabled(text == "Hardset Revision" and self.increment_revision_checkbox.isChecked())

    def update_progress(self, value):
        """Update the progress bar value."""
        self.progress_bar.setValue(value)

    def show_progress_bar(self, visible=True):
        """Show or hide the progress bar."""
        self.progress_bar.setVisible(visible)

    def get_settings(self):
        """Retrieve the current settings from the left menu."""
        settings = {
            "purge_all": self.purge_checkbox.isChecked(),
            "e_transmit": self.transmit_checkbox.isChecked(),
            "increment_revision": self.increment_revision_checkbox.isChecked(),
            "zoom_extents": self.zoom_extents_checkbox.isChecked(),
            "revision_type": self.dropdown.currentText(),
            "hardset_revision": self.hardset_input.text(),
            "attributes": {label: field.text() for label, field in self.text_inputs.items()}
        }
        return settings

    def add_skipped_file(self, filename, error):
        """Add a skipped file and its error to the skipped files list."""
        self.skipped_files_with_errors.append((filename, error))
        self.skipped_button.setText(f"Skipped Files ({len(self.skipped_files_with_errors)})")
        self.skipped_button.setEnabled(True)

    def show_skipped_files(self):
        """Show the skipped files and errors in a dialog."""
        dialog = SkippedFilesDialog(self.skipped_files_with_errors)
        dialog.cleared_signal.connect(self.clear_skipped_files)  # Connect clear signal
        dialog.exec_()

    def clear_skipped_files(self):
        """Clear the skipped files list and update the UI."""
        self.skipped_files_with_errors.clear()  # Reset the skipped files list
        self.skipped_button.setText("Skipped Files (0)")
        self.skipped_button.setEnabled(False)  # Disable the button

    def show_file_summary(self):
        """Show the processed files in a dialog."""
        summary_data = self.drawing_summary_manager.generate_summary()
        summary_view = SummaryView(summary_data, self.drawing_summary_manager)
        summary_view.exec_()


class StreamRedirect:
    """Redirects stdout to a QTextEdit widget."""

    def __init__(self, text_edit):
        self.text_edit = text_edit

    def write(self, text):
        """Write text to the QTextEdit widget."""
        self.text_edit.append(text)

    def flush(self):
        """Required for stream handling."""
        pass
