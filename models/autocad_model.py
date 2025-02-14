import os
import win32com.client
import json5
import time
import comtypes.client

class AutoCADModel:
    @staticmethod
    def _normalize_path(path):
        """Normalize file paths for comparison."""
        return os.path.normcase(os.path.normpath(path))

    @staticmethod
    def get_acad_instance():
        """
        Get the AutoCAD application instance, making it visible.

        Returns:
        - The AutoCAD application instance.

        Raises:
        - RuntimeError if unable to connect to the AutoCAD application.
        """
        try:
            acad = win32com.client.Dispatch("AutoCAD.Application")
            if not acad:
                raise RuntimeError("Unable to connect to AutoCAD.Application instance.")
            return acad
        except Exception as e:
            raise RuntimeError(f"Error initializing AutoCAD instance: {str(e)}")

    @staticmethod
    def get_or_open_document_with_retry(acad, filename, retries=3, delay=1):
        """
        Try to open an AutoCAD document with retry logic.

        Parameters:
        - acad: The AutoCAD application instance.
        - filename: The full path to the file to open.
        - retries: Number of retries if opening fails.
        - delay: Delay (in seconds) between retries.

        Returns:
        - The opened document.

        Raises:
        - RuntimeError if unable to open the document after retries.
        """
        normalized_filename = AutoCADModel._normalize_path(filename)

        if not os.path.exists(filename):
            raise FileNotFoundError(f"The file '{filename}' does not exist.")

        for attempt in range(retries):
            try:
                return acad.Documents.Open(filename)
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(delay)  # Wait before retrying
                else:
                    raise RuntimeError(f"Error opening AutoCAD file {filename} after {retries} retries: {str(e)}")

    @staticmethod
    def extract_attributes_with_retry(filename=None, acad=None, doc=None, layout_name=None, retries=3, delay=1):
        """
        Extracts attribute data from a specific AutoCAD drawing with retry logic.

        Parameters:
        - filename: The full path to the AutoCAD drawing.
        - acad: The AutoCAD application instance (optional).
        - doc: The open AutoCAD document (optional).
        - layout_name: The name of the layout to extract attributes from (optional).
        - retries: Number of retries if extraction fails.
        - delay: Delay (in seconds) between retries.

        Returns:
        - A list of dictionaries with attribute data, including block information.

        Raises:
        - RuntimeError if unable to extract attributes after retries.
        """
        for attempt in range(retries):
            try:
                # If filename is provided, initialize acad and doc
                if filename:
                    acad = acad or AutoCADModel.get_acad_instance()
                    doc = doc or AutoCADModel.get_or_open_document_with_retry(acad, filename)

                data = []

                # Use a specific layout if provided
                layout = None
                if layout_name:
                    layout = next(
                        (l for l in doc.Layouts if l.Name == layout_name),
                        None
                    )
                    if not layout:
                        raise ValueError(f"Layout '{layout_name}' not found in the drawing.")
                else:
                    # Default to the active layout
                    layout = doc.ActiveLayout

                # Extract attributes from the specified layout
                for entity in layout.Block:  # Access entities within this specific layout
                    if entity.EntityName == 'AcDbBlockReference' and entity.HasAttributes:
                        for attrib in entity.GetAttributes():
                            position = attrib.InsertionPoint  # (X, Y, Z)
                            data.append({
                                "Layout": layout.Name,
                                "BlockName": entity.Name,
                                "Tag": attrib.TagString,
                                "Value": attrib.TextString,
                                "Position": {
                                    "X": position[0],
                                    "Y": position[1],
                                    "Z": position[2]
                                },
                            })

                layout = doc.ActiveLayout
                plot_style_table = layout.StyleSheet

                # Save and close the document if filename is provided
                if filename:
                    try:
                        doc.Save()
                        doc.Close()
                    except Exception as save_close_error:
                        print(f"Error saving/closing file {filename}: {str(save_close_error)}")

                return data, plot_style_table

            except Exception as e:
                # Retry logic
                if attempt < retries - 1:
                    time.sleep(delay)  # Wait before retrying
                else:
                    # Raise error after all retries fail
                    raise RuntimeError(
                        f"Error extracting attributes after {retries} retries for file {filename}: {str(e)}")


    @staticmethod
    def write_attributes_with_retry(acad, doc, updates, retries=3, delay=1):
        """
        Write attribute values back to AutoCAD with retry logic.

        Parameters:
        - acad: The AutoCAD instance.
        - doc: The open AutoCAD document.
        - updates: A list of dictionaries where each dictionary contains:
                       - "Layout": (Optional) The name of the layout.
                       - "BlockName": (Optional) The name of the block reference.
                       - "Tag": The attribute tag to update.
                       - "Value": The new value to set.
        - retries: Number of retries if writing fails.
        - delay: Delay (in seconds) between retries.

        Raises:
        - RuntimeError if unable to write attributes after retries.
        """
        for attempt in range(retries):
            try:
                for update in updates:
                    layout_name = update.get("Layout")  # Optional
                    block_name = update.get("BlockName")  # Optional
                    tag = update["Tag"]
                    new_value = update["Value"]

                    # Iterate over all layouts or target a specific one
                    for layout in (
                    doc.Layouts if not layout_name else [l for l in doc.Layouts if l.Name == layout_name]):
                        # Iterate over entities in the layout
                        for entity in layout.Block:
                            if entity.EntityName == 'AcDbBlockReference' and (
                                    not block_name or entity.Name == block_name):
                                if entity.HasAttributes:
                                    for attrib in entity.GetAttributes():
                                        if attrib.TagString == tag:
                                            attrib.TextString = new_value
                                            attrib.Update()  # Commit the change
                return  # Exit function if successful
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(delay)  # Wait before retrying
                else:
                    raise RuntimeError(f"Error writing attributes to AutoCAD after {retries} retries: {str(e)}")

    @staticmethod
    def print_fields_as_json5(data):
        """
        Prints extracted fields in JSON5 format for easy copying.

        Parameters:
        - data: List of dictionaries containing attribute data.
        """
        json5_output = {}

        for item in data:
            tag = item.get("Tag", "")
            value = item.get("Value", "")
            json5_output[tag] = value

        print("// Extracted fields in JSON5 format:")
        print(json5.dumps(json5_output, indent=4))

    @staticmethod
    def zoom_extents(acad, doc):
        """
        Trigger a Zoom Extents command in AutoCAD.

        Parameters:
        - acad: The AutoCAD instance.
        - doc: The open AutoCAD document.

        Raises:
        - RuntimeError if the command fails.
        """
        try:
            if not doc:
                raise ValueError("No document is active to execute Zoom Extents.")

            # Switch focus to the document
            acad.ActiveDocument = doc

            # Send the Zoom Extents command to AutoCAD
            doc.SendCommand("ZOOM\nE\n")
        except Exception as e:
            raise RuntimeError(f"Error executing Zoom Extents: {str(e)}")

    @staticmethod
    def purge_all(acad, doc):
        """
        Trigger a Zoom Extents command in AutoCAD.

        Parameters:
        - acad: The AutoCAD instance.
        - doc: The open AutoCAD document.

        Raises:
        - RuntimeError if the command fails.
        """
        try:
            if not doc:
                raise ValueError("No document is active to execute Zoom Extents.")

            # Switch focus to the document
            acad.ActiveDocument = doc

            # Send the Zoom Extents command to AutoCAD
            doc.SendCommand("-PURGE\nALL\n*\nN\n")
        except Exception as e:
            raise RuntimeError(f"Error executing Zoom Extents: {str(e)}")

    @staticmethod
    def etransmit(acad, doc):
        """
        Trigger a Zoom Extents command in AutoCAD.

        Parameters:
        - acad: The AutoCAD instance.
        - doc: The open AutoCAD document.

        Raises:
        - RuntimeError if the command fails.
        """
        try:
            if not doc:
                raise ValueError("No document is active to execute Zoom Extents.")

            # Switch focus to the document
            acad.ActiveDocument = doc

            # Send the Zoom Extents command to AutoCAD
            doc.SendCommand("etrans\n")
        except Exception as e:
            raise RuntimeError(f"Error executing Zoom Extents: {str(e)}")


    @staticmethod
    def rename_layouts(acad, doc):
        """
        Trigger a Zoom Extents command in AutoCAD.

        Parameters:
        - acad: The AutoCAD instance.
        - doc: The open AutoCAD document.

        Raises:
        - RuntimeError if the command fails.
        """
        try:
            if not doc:
                raise ValueError("No document is active to execute layout rename.")

            # Switch focus to the document
            acad.ActiveDocument = doc

            # Send the Zoom Extents command to AutoCAD
            doc.SendCommand("RENAMELAYOUTS\n")
        except Exception as e:
            raise RuntimeError(f"Error executing Layout Rename: {str(e)}")

    @staticmethod
    def plot_to_pdf(plot_style: str, doc_name: str, file_path, doc, acad):
        """
        Triggers a plot command in AutoCAD.

        Parameters:
        - plot_style (str): The CTB plot style file.
        - doc_name (str): The document name for the plot.
        - doc: The open AutoCAD document.
        - acad: The AutoCAD instance.

        Raises:
        - RuntimeError if the command fails.
        """
        try:
            if not doc:
                raise ValueError("No document is active to execute plot.")

            # Switch focus to the document
            acad.ActiveDocument = doc

            root_folder = os.path.dirname(file_path)
            new_path = os.path.join(root_folder, doc_name)
            print(f"New path = {new_path}")

            # Properly format the command with arguments
            command = f'PLOTCURRENTLAYOUT\n {new_path}\n "{plot_style}"\n'

            # Send the plot command to AutoCAD
            doc.SendCommand(command)

        except Exception as e:
            raise RuntimeError(f"Error plotting: {str(e)}")

    @staticmethod
    def get_plot_style_table():
        try:
            acad = comtypes.client.GetActiveObject("AutoCAD.Application")
            doc = acad.ActiveDocument

            # Retrieve the plot settings for the active layout
            layout = doc.ActiveLayout
            plot_style_table = layout.StyleSheet  # This gets the currently assigned CTB file

            if plot_style_table:
                return plot_style_table
            else:
                print("No CTB (Plot Style) file detected.")

        except Exception as e:
            print(f"Error: {e}")

