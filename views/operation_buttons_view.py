from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton


class OperationButtonsView(QWidget):
    # Define signals for button actions
    extract_signal = pyqtSignal()
    visualise_signal = pyqtSignal()
    run_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()

        # Button 1: Extract Sample Fields
        self.extract_button = QPushButton("Extract Sample Fields")
        self.extract_button.clicked.connect(self.extract_signal.emit)
        layout.addWidget(self.extract_button)

        # # Button 2: Visualise Fields
        # self.visualise_button = QPushButton("Visualise Fields")
        # self.visualise_button.setEnabled(False)  # Initially disabled
        # self.visualise_button.clicked.connect(self.visualise_signal.emit)
        # layout.addWidget(self.visualise_button)

        # Button 3: Run
        self.run_button = QPushButton("Run")
        self.run_button.setEnabled(False)  # Initially disabled
        self.run_button.clicked.connect(self.run_signal.emit)
        layout.addWidget(self.run_button)

        self.setLayout(layout)
    #
    # def enable_visualise_button(self):
    #     """Enable the Visualise Fields button."""
    #     self.visualise_button.setEnabled(True)

    def enable_run_button(self):
        """Enable the Visualise Fields button."""
        self.run_button.setEnabled(True)

