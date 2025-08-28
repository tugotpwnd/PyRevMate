import os
from PyQt5.QtCore import QObject, pyqtSignal, QCoreApplication
from PyQt5.QtWidgets import QMessageBox
import traceback
import time
from time import sleep
from models.autocad_model import AutoCADModel  # Assuming your AutoCAD logic is encapsulated here
from models.increment_revision_model import modify_table_data_to_increment_revision
from models.file_consistency_model import CrucialFieldValidator


class RunModel(QObject):
    progress_signal = pyqtSignal(int)  # Signal to report progress percentage
    error_signal = pyqtSignal(str)  # Signal to report errors
    finished_signal = pyqtSignal()  # Signal when the operation is complete
    process_aborted_signal = pyqtSignal()

    def __init__(self, settings, folder_path, table_data, left_menu, file_path):
        """
        Initialize the RunModel.

        Parameters:
        - settings: Dictionary containing the user's settings.
        - folder_path: Path to the folder containing AutoCAD files.
        - table_data: The initial table data to validate against.
        - left_menu: The UI's left menu component for logging skipped files.
        """
        super().__init__()
        self.settings = settings
        self.folder_path = folder_path
        self.table_data = table_data
        self.left_menu = left_menu
        self.file_path = file_path
        self.stop_requested = False
        self.field_validator = CrucialFieldValidator(table_data)

    def request_stop(self):
        """Set the stop flag to True."""
        self.stop_requested = True

    def start(self):
        """Start the batch processing operation."""
        try:
            files = self.get_autocad_files(self.folder_path)
            total_files = len(files)

            if total_files == 0:
                self.error_signal.emit("No AutoCAD files found in the folder.")
                return

            for index, file in enumerate(files):
                # Check if stop is requested
                if self.stop_requested:
                    self.process_aborted_signal.emit()
                    print("Processing stopped by user.")
                    break

                acad = AutoCADModel.get_acad_instance()
                try:
                    self.process_file(acad, file)
                except Exception as e:
                    self.error_signal.emit(f"Error processing file {file}: {str(e)}")

                progress = int(((index + 1) / total_files) * 100)
                self.progress_signal.emit(progress)

                # Pause after processing the first file to get user confirmation
                if index == 0:
                    user_response = self.get_user_confirmation()
                    if not user_response:
                        self.process_aborted_signal.emit()
                        print("User chose not to proceed after the first file.")
                        return  # Exit the operation if the user declines to continue

                # Process Qt events to keep the UI responsive
                QCoreApplication.processEvents()

            self.finished_signal.emit()

        except Exception as e:
            self.error_signal.emit(f"An error occurred: {str(e)}")

    def get_user_confirmation(self):
        """Ask the user for confirmation to continue."""
        reply = QMessageBox.question(
            None,
            "Continue Processing?",
            "The first file has been processed. Please review it in AutoCAD and"
            " confirm you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
        )
        return reply == QMessageBox.Yes

    def get_autocad_files(self, folder_path):
        """Get a list of all AutoCAD files in the folder."""
        return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.dwg')]

    def process_file(self, acad, filename):
        """Process an individual AutoCAD file."""
        doc = None
        layouts = []
        try:
            # Step 1: Get AutoCAD instance and open the document
            try:
                doc = AutoCADModel.get_or_open_document_with_retry(acad, filename)
            except Exception as e:
                self.left_menu.add_skipped_file(filename, f"Error opening AutoCAD file: {str(e)}\n{traceback.format_exc()}")
                return  # Skip the file

            # Step 2: Retry logic for layouts
            try:
                for attempt in range(3):  # Retry up to 3 times
                    try:
                        layouts = list(doc.Layouts)  # Force enumeration to check readiness
                        break  # Exit retry loop if successful
                    except Exception as layout_error:
                        if attempt < 2:  # Retry twice before failing
                            time.sleep(1)  # Delay before retrying
                        else:
                            self.left_menu.add_skipped_file(filename,
                                                  f"Failed to enumerate layouts: {str(layout_error)}\n{traceback.format_exc()}")
                            return  # Skip the file
            except Exception as e:
                self.left_menu.add_skipped_file(filename, f"Error processing layouts: {str(e)}\n{traceback.format_exc()}")
                return  # Skip the file

            # Step 3: Iterate over layouts with retry logic
            for layout in layouts:
                # Retry mechanism for accessing layout properties
                layout_name = None
                for attempt in range(3):  # Retry up to 3 times
                    try:
                        layout_name = layout.Name
                        break  # Exit retry loop if successful
                    except Exception as e:
                        if attempt < 2:  # Retry twice before failing
                            sleep(1)  # Wait before retrying
                        else:
                            self.left_menu.add_skipped_file(
                                f"{filename} - <Unknown Layout>",
                                f"Error accessing layout name: {str(e)}\n{traceback.format_exc()}"
                            )
                            continue  # Skip this layout after retries

                if not layout_name or layout_name == 'Model':  # Skip model space or failed layout
                    continue

                    # Step 3.1: Retry logic for activating the layout
                for attempt in range(3):  # Retry up to 3 times
                    try:
                        doc.ActiveLayout = layout  # Switch to the current layout
                        break  # Exit retry loop if successful
                    except Exception as e:
                        if attempt < 2:  # Retry twice before failing
                            time.sleep(1)  # Wait before retrying
                        else:
                            self.left_menu.add_skipped_file(
                                f"{filename} - {layout_name}",
                                f"Error activating layout after 3 attempts: {str(e)}\n{traceback.format_exc()}"
                            )
                            continue  # Skip this layout after retries

                # Rename layout if enabled in settings and it is numeric
                if self.settings.get("rename_sheets", False):
                    AutoCADModel.rename_layouts(acad, doc)

                # Retry logic for extracting attributes
                try:
                    for attempt in range(3):  # Retry up to 3 times
                        try:
                            layout_data, _ = AutoCADModel.extract_attributes_with_retry(
                                acad=acad, doc=doc, layout_name=layout_name
                            )
                            break  # Exit retry loop if successful
                        except Exception as e:
                            if attempt < 2:  # Retry twice before failing
                                sleep(1)  # Wait before retrying
                            else:
                                self.left_menu.add_skipped_file(
                                    f"{filename} - {layout_name}",
                                    f"Error extracting attributes: {str(e)}\n{traceback.format_exc()}"
                                )
                                continue  # Skip this layout after retries

                    # If layout_data was not retrieved, skip this layout
                    if not layout_data:
                        self.left_menu.add_skipped_file(
                            f"{filename} - {layout_name}",
                            f"There was no layout data retrieved from the document."
                        )
                        continue

                    # Check that all the fields are consistent across the documents.
                    missing_fields = self.field_validator.validate(layout_data)
                    if missing_fields:
                        self.left_menu.add_skipped_file(
                            f"{filename} - {layout_name}",
                            f"The following fields are missing from the layout : {missing_fields}"
                        )
                        continue

                except Exception as e:
                    self.left_menu.add_skipped_file(
                        f"{filename} - {layout_name}",
                        f"Error during attribute extraction: {str(e)}\n{traceback.format_exc()}"
                    )
                    continue  # Skip this layout

                # Retry logic for mapping layout data to table data
                try:
                    new_data = None
                    for attempt in range(3):  # Retry up to 3 times
                        try:
                            new_data = map_extracted_data_to_table(self.table_data, layout_data, layout_name)
                            break  # Exit retry loop if successful
                        except Exception as e:
                            if attempt < 2:  # Retry twice before failing
                                sleep(1)  # Wait before retrying
                            else:
                                self.left_menu.add_skipped_file(
                                    f"{filename} - {layout_name}",
                                    f"Error mapping data: {str(e)}\n{traceback.format_exc()}"
                                )
                                continue  # Skip this layout after retries

                    # If new_data was not retrieved, skip this layout
                    if not new_data:
                        continue

                except Exception as e:
                    self.left_menu.add_skipped_file(
                        f"{filename} - {layout_name}",
                        f"Error during data mapping: {str(e)}\n{traceback.format_exc()}"
                    )
                    continue  # Skip this layout

                # Process updates (if needed)
                updated_data = None
                try:
                    if self.settings.get("increment_revision", True):
                        revision_type = self.settings.get("revision_type", None)
                        hardset_revision = self.settings.get("hardset_revision", None)
                        attributes = self.settings.get("attributes", None)

                        if revision_type is None or attributes is None:
                            raise ValueError("Missing revision settings.")

                        updated_data = modify_table_data_to_increment_revision(
                            revision_type, hardset_revision, attributes, new_data, layout.Name
                        )
                except Exception as e:
                    self.left_menu.add_skipped_file(f"{filename} - {layout.Name}",
                                          f"Error modifying table data: {str(e)}\n{traceback.format_exc()}")
                    continue  # Skip this layout

                try:
                    # Add static assignments to updated data
                    updated_data_with_static = add_static_assignments(
                        self.table_data, updated_data, layout.Name
                    )
                except Exception as e:
                    self.left_menu.add_skipped_file(f"{filename} - {layout.Name}",
                                          f"Error adding static assignments: {str(e)}\n{traceback.format_exc()}")
                    continue  # Skip this layout

                if self.settings.get("read_replace_enabled", False):
                    try:
                        read_for = self.settings.get("read_replace_data", {})
                        updated_data_with_static = read_replace_assignments(
                            layout_data, updated_data_with_static, read_for, layout.Name
                        )
                    except Exception as e:
                        self.left_menu.add_skipped_file(
                            f"{filename} - {layout.Name}",
                            f"Error adding read-replace assignments: {str(e)}\n{traceback.format_exc()}",
                        )
                        continue

                try:
                    # Write updates to AutoCAD
                    if updated_data_with_static:
                        AutoCADModel.write_attributes_with_retry(acad, doc, updates=updated_data_with_static)
                except Exception as e:
                    self.left_menu.add_skipped_file(f"{filename} - {layout.Name}",
                                          f"Error writing attributes: {str(e)}\n{traceback.format_exc()}")
                    continue  # Skip this layout

                try:
                    # Perform additional commands
                    if self.settings.get("zoom_extents", True):
                        AutoCADModel.zoom_extents(acad, doc)
                    if self.settings.get("purge_all", True):
                        AutoCADModel.purge_all(acad, doc)
                except Exception as e:
                    self.left_menu.add_skipped_file(f"{filename} - {layout.Name}",
                                          f"Error executing additional commands: {str(e)}\n{traceback.format_exc()}")
                    continue  # Skip this layout

                dwg_value = None
                revision_value = None
                try:
                    if self.settings.get("plot_to_pdf", True):
                        for item in new_data:
                            if item["Assignment"] == "DWG No.":
                                dwg_value = item["Value"]
                                print(dwg_value)
                            elif item["Assignment"] == "REVISION":
                                revision_value = item["Value"]
                                print(f"rev value 1: {revision_value}")

                        for item in updated_data_with_static:
                            if item["Assignment"] == "REVISION":
                                revision_value = item["Value"]
                                print(f"rev value 2 : {revision_value}")

                        if dwg_value and revision_value:
                            print("There is a dwg val")
                        else:
                            print(f"Either dwg_value : {dwg_value} or revision value: {revision_value} is missing")

                        if dwg_value and revision_value:

                            pdf_name = f"{dwg_value}_{revision_value}"

                            print(f"pdf name is : {pdf_name}")

                            plot_style = self.settings.get("plot_style_table")

                            AutoCADModel.plot_to_pdf(plot_style, pdf_name, self.file_path, doc, acad)
                        else:
                            print("Missing DWG or ISSUE value, skipping plot to PDF.")

                except Exception as e:
                    self.left_menu.add_skipped_file(f"{filename} - {layout.Name}",
                                                    f"Error executing additional commands: {str(e)}\n{traceback.format_exc()}")
                    continue  # Skip this layout

                # Append the drawing to the summary
                self.left_menu.drawing_summary_manager.add_layout(new_data, updated_data_with_static)

            # Moved to outside layout loop.
            if self.settings.get("e_transmit", True):
                AutoCADModel.etransmit(acad, doc)

        except Exception as e:
            self.left_menu.add_skipped_file(filename, f"Error processing file: {str(e)}\n{traceback.format_exc()}")
        finally:
            if doc:
                def save_and_close_document():
                    doc.Save()
                    doc.Close()

                for attempt in range(3):  # Retry up to 3 times
                    try:
                        save_and_close_document()
                        break  # Exit loop if successful
                    except Exception as e:
                        if attempt < 2:  # Retry twice before logging an error
                            time.sleep(1)  # Delay before retrying
                        else:
                            print(f"Error saving/closing file {filename}: {str(e)}")


def map_extracted_data_to_table(table_data, layout_data, layout_name):
    """
    Maps extracted layout data to the corresponding table data fields.

    Parameters:
    - table_data: Original table data containing assignment mappings and static values.
    - layout_data: Data extracted from a specific AutoCAD layout.
    - layout_name: The name of the layout being processed.

    Returns:
    - A list of dictionaries with mapped data, including the layout name.
    """
    mapped_data = []  # Initialize the list to store the mapped data

    for entry in layout_data:
        # Iterate over each extracted entry from the layout
        for field in table_data:
            # Match the entries based on the Tag field
            if field["Tag"] == entry["Tag"]:
                mapped_data.append({
                    "Tag": field["Tag"],  # Copy the Tag from table_data
                    "Assignment": field.get("Assignment", ""),  # Get Assignment or default to an empty string
                    "Value": entry["Value"],  # Use the extracted Value from the layout
                    "StaticValue": field.get("StaticValue", ""),  # Get StaticValue or default to an empty string
                    "Layout": layout_name  # Attach the layout name to the entry
                })

    return mapped_data  # Return the mapped data with layout information


def add_static_assignments(table_data, updated_data=None, layout_name=None):
    """
    Adds static assignments from table_data to updated_data.

    Parameters:
    - table_data: Original table data containing static assignments.
    - updated_data: The list of updated data to add static assignments to (default: None).
    - layout_name: The name of the layout being processed.

    Returns:
    - The updated list of dictionaries, including all static assignments.
    """
    if updated_data is None:
        updated_data = []  # Initialize updated_data as an empty list if not provided

    # Identify all fields in table_data with Assignment == "STATIC"
    static_assignments = [
        field for field in table_data if field.get("Assignment") == "STATIC"
    ]

    for static_field in static_assignments:
        # Add the static field to updated_data, using StaticValue if present or leaving Value blank
        updated_data.append({
            "Tag": static_field["Tag"],  # Copy the Tag from table_data
            "Assignment": static_field["Assignment"],  # Copy the Assignment from table_data
            "Value": static_field.get("StaticValue", ""),  # Use StaticValue or empty string as the Value
            "StaticValue": static_field.get("StaticValue", ""),  # Retain the StaticValue
            "Layout": layout_name  # Attach the layout name to the entry
        })

    return updated_data  # Return the updated data, including all static assignments


def read_replace_assignments(table_data, updated_data=None, read_for=None, layout_name=None):
    if updated_data is None:
        updated_data = []
    if read_for is None:
        read_for = {}
    updated_data_dict = {item['Tag']: item for item in updated_data}
    for item in table_data:
        tag = item.get('Tag')
        value = item.get('Value')
        if value in read_for:
            new_value = read_for[value]
            item['Value'] = new_value
            if tag in updated_data_dict:
                updated_data_dict[tag]['Value'] = new_value
            else:  # inserted
                updated_data_dict[tag] = {'Tag': tag, 'Assignment': item.get('Assignment', ''), 'Value': new_value, 'StaticValue': item.get('StaticValue', ''), 'Layout': layout_name}
    updated_data = list(updated_data_dict.values())
    return updated_data

