from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QFileDialog, QMessageBox
)
import pandas as pd


class SummaryView(QDialog):
    """A dialog to display the drawing summary in a table format with an export button."""

    def __init__(self, summary_data, drawing_summary_manager):
        """
        Initialize the SummaryView.

        Parameters:
        - summary_data: List of dictionaries containing the drawing summaries.
        """
        super().__init__()
        self.setWindowTitle("Drawing Summary")
        self.setMinimumSize(600, 400)

        self.summary_data = summary_data
        self.drawing_summary_manager = drawing_summary_manager

        # Layout setup
        layout = QVBoxLayout()

        # Table for displaying summary data
        self.table = QTableWidget(len(summary_data), 4)
        self.table.setHorizontalHeaderLabels(["Revision", "Revision Description", "Drawing Number", "Drawing Title"])
        self.populate_table()
        layout.addWidget(self.table)

        # Export button
        self.export_button = QPushButton("Export to Excel")
        self.export_button.clicked.connect(self.export_to_excel)
        layout.addWidget(self.export_button)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear)
        layout.addWidget(clear_button)

        self.setLayout(layout)

    def populate_table(self):
        """Populate the table with summary data."""
        for row, summary in enumerate(self.summary_data):
            self.table.setItem(row, 0, QTableWidgetItem(summary["Revision"]))
            self.table.setItem(row, 1, QTableWidgetItem(summary["Revision Description"]))
            self.table.setItem(row, 2, QTableWidgetItem(summary["Drawing Number"]))
            self.table.setItem(row, 3, QTableWidgetItem(summary["Drawing Title"]))

    def export_to_excel(self):
        """Export the summary data to an Excel file."""
        try:
            # Open a file dialog to select the save location
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Summary to Excel", "", "Excel Files (*.xlsx);;All Files (*)", options=options
            )

            if file_path:
                # Create a DataFrame from the summary data
                df = pd.DataFrame(self.summary_data)

                # Save to Excel
                df.to_excel(file_path, index=False)

                # Confirmation message
                QMessageBox.information(self, "Export Successful", "Summary successfully exported to Excel.")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"An error occurred while exporting to Excel:\n{str(e)}")

    def clear(self):
        """Clear the table and reset skipped files."""
        self.table.clearContents()  # Clears the contents of the table
        self.table.setRowCount(0)  # Resets the number of rows to 0
        self.drawing_summary_manager.clear()
