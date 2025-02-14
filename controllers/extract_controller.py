from PyQt5.QtCore import QObject, pyqtSignal
from utils.helpers import is_autocad_running, open_autocad_file_dialog
from models.autocad_model import AutoCADModel
from models.increment_revision_model import get_revision_fields


class ExtractController(QObject):
    error_signal = pyqtSignal(str)  # Signal to emit error messages
    data_ready_signal = pyqtSignal(list, str, str)  # First is list, second is str

    def __init__(self):
        super().__init__()
        self.used_fields = set()

    def handle_extract(self):
        """Handle the extraction of AutoCAD attributes."""
        # Open file dialog to select AutoCAD drawing
        filename = open_autocad_file_dialog()
        if not filename:
            self.error_signal.emit("No file selected.")
            return

        try:
            # Extract attributes from the selected file
            data, plot_style_table = AutoCADModel.extract_attributes_with_retry(filename=filename)

            self.data_ready_signal.emit(data, plot_style_table, filename)  # Notify the view with the data
        except RuntimeError as e:
            self.error_signal.emit(f"Failed to extract data: {str(e)}")

