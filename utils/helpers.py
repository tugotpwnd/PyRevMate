import win32com.client
import json5
import os
import sys


def format_text(text):
    """Example utility function to format text (if needed)."""
    return text.upper()  # Example transformation


def is_autocad_running():
    """Check if AutoCAD is running."""
    try:
        win32com.client.Dispatch("AutoCAD.Application")
        return True
    except Exception:
        return False


from PyQt5.QtWidgets import QFileDialog


def open_autocad_file_dialog():
    """Open a file dialog to select an AutoCAD file."""
    options = QFileDialog.Options()
    options |= QFileDialog.ReadOnly
    filename, _ = QFileDialog.getOpenFileName(
        None,
        "Select AutoCAD Drawing",
        "",
        "AutoCAD Files (*.dwg);;All Files (*)",
        options=options
    )
    return filename


def select_drawing_folder():
    """
    Open a dialog to select a folder containing AutoCAD drawings.

    Returns:
    - The selected folder path as a string.
    """
    folder = QFileDialog.getExistingDirectory(
        None,
        "Select Folder Containing AutoCAD Drawings",
        "",
        QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
    )
    return folder

def resource_path(relative_path):
    """
    Get the absolute path to a resource, works for PyInstaller and during development.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Fallback for regular development environment
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def load_mapping_from_json(filepath):
    """
    Load the tag-to-assignment mapping from a JSON5 file.

    Parameters:
    - filepath: Path to the JSON5 file.

    Returns:
    - Dictionary containing tag-to-assignment mappings.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"JSON5 file not found: {filepath}")

    with open(filepath, "r") as file:
        try:
            return json5.load(file)
        except json5.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON5 format in file: {filepath}. Error: {str(e)}")

