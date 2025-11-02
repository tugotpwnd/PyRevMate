# utils/helpers.py
import win32com.client
import json5
import os
import sys
from PyQt5.QtWidgets import QFileDialog

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
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def _ensure_parent_dir(path: str):
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

def load_mapping_from_json(filepath):
    """
    Load the tag-to-assignment mapping from a JSON5 file.
    """
    if not os.path.exists(filepath):
        # First run: create an empty file
        _ensure_parent_dir(filepath)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("{}\n")
        return {}
    with open(filepath, "r", encoding="utf-8") as file:
        try:
            return json5.load(file)
        except json5.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON5 format in file: {filepath}. Error: {str(e)}")

def save_mapping_to_json(filepath, mapping: dict):
    """
    Save (overwrite) the mapping to JSON5. Caller should pass final merged dict.
    """
    if not isinstance(mapping, dict):
        raise ValueError("Mapping must be a dictionary.")
    _ensure_parent_dir(filepath)
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(json5.dumps(mapping, indent=2) + "\n")
