# controllers/main_controller.py
from views.main_view import MainView
from controllers.extract_controller import ExtractController
from controllers.run_controller import RunController
from utils.helpers import select_drawing_folder
from models.run_model import RunModel
from utils.settings import Settings
from models.logger_model import DrawingSummaryManager
from views.mapping_dialog import MapFieldsDialog  # NEW

class MainController:
    def __init__(self):
        self.drawing_summary_manager = DrawingSummaryManager()
        self.view = MainView(self.drawing_summary_manager)
        self.extract_controller = ExtractController()
        self.settings = Settings()
        self.settings.error_signal.connect(self.view.show_error)

        # Store data for table and visualization
        self.data = None
        self.plot_style_table = None
        self.file_path = None

        # Instantiate the run model
        self.run_model = None

        # Signals best read right to left.
        # Extract Controller -> Main Controller
        self.extract_controller.data_ready_signal.connect(self.handle_data_ready)
        self.extract_controller.error_signal.connect(self.view.show_error)

        # OperationsButtons -> MainController
        self.view.operation_buttons.extract_signal.connect(self.extract_controller.handle_extract)
        self.view.operation_buttons.run_signal.connect(self.handle_run)

        # NEW: LeftMenu "Map Fields…" button -> open mapping dialog
        self.view.left_menu.map_fields_signal.connect(self.open_map_fields_dialog)

    def handle_data_ready(self, data, plot_style_table, file_path):
        """Handle data ready signal."""
        self.data = data
        self.plot_style_table = plot_style_table
        self.file_path = file_path
        self.view.left_menu.plot_style_text_box.setText(plot_style_table)

        self.view.viewport.populate_table(data)
        self.view.operation_buttons.enable_run_button()

    def handle_run(self):
        """Handle the Run button click."""
        folder_path = select_drawing_folder()
        if not folder_path:
            self.view.show_error("No folder selected.")
            return

        specified_settings = self.view.left_menu.get_settings()
        table_data = self.view.viewport.extract_all_table_data()

        if not self.settings.validate(table_data, specified_settings):
            return

        self.run_model = RunModel(specified_settings, folder_path, table_data, self.view.left_menu, self.file_path)
        self.view.left_menu.set_run_model(self.run_model)

        self.run_model.progress_signal.connect(self.view.left_menu.update_progress)
        self.run_model.error_signal.connect(self.view.show_error)
        self.run_model.finished_signal.connect(self.handle_run_finished)
        self.run_model.process_aborted_signal.connect(self.handle_process_aborted)

        self.view.left_menu.show_progress_bar(True)
        self.run_model.start()

    def open_map_fields_dialog(self):
        """
        Open the Map Fields dialog using current extracted fields and assignment options.
        After saving, reload mapping and refresh colors in the main table.
        """
        if not self.data:
            self.view.show_error("Load a sample first (Extract Sample Fields) before mapping.")
            return

        assignment_options = self.view.viewport.assignment_options
        mapping_path = self.view.viewport.get_mapping_filepath()

        # Robust import (flat or package)
        try:
            from views.mapping_dialog import MapFieldsDialog
        except Exception:
            from mapping_dialog import MapFieldsDialog

        dlg = MapFieldsDialog(
            extracted_fields=self.data,
            assignment_options=assignment_options,
            mapping_filepath=mapping_path,
            parent=self.view
        )
        if dlg.exec_() == dlg.Accepted:
            # 1) reload mapping used by the main table
            self.view.viewport.reload_tag_to_assignment()
            # 2) recolor rows so mapped lines go green immediately
            self.view.viewport.refresh_row_colors()

    def disable_unused_fields(self, unused_fields):
        for field in unused_fields:
            print(field)

    def handle_process_aborted(self):
        self.view.left_menu.update_progress(0)
        self.view.left_menu.show_progress_bar(False)

    def handle_run_finished(self):
        """Handle the completion of the RunModel."""
        self.view.left_menu.update_progress(0)
        self.view.left_menu.show_progress_bar(False)

    def run(self):
        self.view.show()
