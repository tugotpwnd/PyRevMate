from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QLabel, QMessageBox
from views.left_menu_view import LeftMenuView
from views.operation_buttons_view import OperationButtonsView
from views.viewport_view import ViewportView


class MainView(QMainWindow):
    # Define custom signals
    extract_signal = pyqtSignal()
    run_signal = pyqtSignal()

    def __init__(self, drawing_summary_manager):
        super().__init__()
        self.drawing_summary_manager = drawing_summary_manager
        self.setWindowTitle("PyRev Mate V_1.8")
        self.setGeometry(0, 0, 1920, 1080)

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Left menu (Settings)
        self.left_menu = LeftMenuView(self.drawing_summary_manager)
        self.left_menu.setFixedWidth(self.width() // 4)  # Fixed to 1/4 of the window width
        main_layout.addWidget(self.left_menu)

        # Right layout for operations and viewport
        right_layout = QVBoxLayout()

        # Title and description
        title_label = QLabel("PyRev Mate V_1.8")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        right_layout.addWidget(title_label)

        description_label = QLabel("A tool to extract and manage AutoCAD attributes.")
        description_label.setWordWrap(True)
        right_layout.addWidget(description_label)

        # Operation buttons
        self.operation_buttons = OperationButtonsView()
        right_layout.addWidget(self.operation_buttons)

        # Connect OperationButtonsView signals to MainView signals
        self.operation_buttons.extract_signal.connect(self.extract_signal.emit)
        self.operation_buttons.run_signal.connect(self.run_signal.emit)

        # Add Viewport
        self.viewport = ViewportView()
        right_layout.addWidget(self.viewport)

        # Add right layout to main layout
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget)

    def show_error(self, message):
        """Display an error message."""
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText(message)
        error_dialog.exec_()

    def get_settings(self):
        """Retrieve settings from the UI."""
        settings = {
            "purge": self.left_menu.purge_checkbox.isChecked(),
            "rename": self.left_menu.rename_checkbox.isChecked(),
            "plot": self.left_menu.plot_to_pdf_checkbox.isChecked(),
            "plot_style_table": self.left_menu.plot_style_text_box.text(),
            "transmit": self.left_menu.transmit_checkbox.isChecked(),
            "increment_revision": self.left_menu.increment_revision_checkbox.isChecked(),
            "revision_type": self.left_menu.dropdown.currentText(),
            "hardset_revision": self.left_menu.hardset_input.text() if self.left_menu.dropdown.currentText() == "Hardset Revision" else None,
            "attributes": {label: field.text() for label, field in self.left_menu.text_inputs.items()},
        }
        return settings
