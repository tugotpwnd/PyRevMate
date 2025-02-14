from views.main_view import MainView
from controllers.extract_controller import ExtractController
from controllers.run_controller import RunController
from utils.helpers import select_drawing_folder
from models.run_model import RunModel
from utils.settings import Settings
from models.logger_model import DrawingSummaryManager


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
        # Signal path / Extract Controller -> Main Controller
        self.extract_controller.data_ready_signal.connect(self.handle_data_ready)
        # Signal path / Extract Controller -> Main Controller - > MainWindow (Method Call) : Show Error
        self.extract_controller.error_signal.connect(self.view.show_error)

        # Signal path /  OperationsButtons - > MainWindow - > Main Controller (Method Call) : Extract Controller
        self.view.operation_buttons.extract_signal.connect(self.extract_controller.handle_extract)

        # Connect the Run button signal
        self.view.operation_buttons.run_signal.connect(self.handle_run)

    def handle_data_ready(self, data, plot_style_table, file_path):
        """Handle data ready signal."""
        self.data = data  # Store the data for later use
        self.plot_style_table = plot_style_table
        self.file_path = file_path
        self.view.left_menu.plot_style_text_box.setText(plot_style_table)

        self.view.viewport.populate_table(data)  # Populate table in the viewport
        # self.view.operation_buttons.enable_visualise_button()  # Enable Visualise button
        self.view.operation_buttons.enable_run_button()  # Enable assign button

    def handle_run(self):
        """Handle the Run button click."""
        # Select the folder containing AutoCAD files
        folder_path = select_drawing_folder()
        if not folder_path:
            self.view.show_error("No folder selected.")
            return

        # Retrieve settings from the LeftMenuView
        specified_settings = self.view.left_menu.get_settings()

        # Collect all table data from the ViewportView
        table_data = self.view.viewport.extract_all_table_data()

        # Validate there are no errors in the users setting selection
        if not self.settings.validate(table_data, specified_settings):
            return  # Exit if validation fails

        # Initialize the RunModel with the required data
        self.run_model = RunModel(specified_settings, folder_path, table_data, self.view.left_menu, self.file_path)
        self.view.left_menu.set_run_model(self.run_model)  # Pass RunModel to LeftMenuView

        # Connect RunModel signals to handle progress and errors
        self.run_model.progress_signal.connect(self.view.left_menu.update_progress)
        self.run_model.error_signal.connect(self.view.show_error)
        self.run_model.finished_signal.connect(self.handle_run_finished)
        self.run_model.process_aborted_signal.connect(self.handle_process_aborted)

        # Show the progress bar and start processing
        self.view.left_menu.show_progress_bar(True)
        self.run_model.start()

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
        pass

    def run(self):
        self.view.show()
