from PyQt5.QtCore import pyqtSignal, QObject


class Settings(QObject):  # Ensure it's a QObject to use signals
    error_signal = pyqtSignal(str)  # Signal to report errors

    def __init__(self):
        super().__init__()
        self.errors = set()  # Use a set to avoid duplicate error messages
        self.used_fields = set()

    def validate(self, table_data, settings):
        """Validate the user's settings."""
        self.errors.clear()  # Clear any previous errors

        # Example validation logic
        if settings["revision_type"] == "Hardset Revision" and not settings["hardset_revision"]:
            self.errors.add("Hardset Revision requires a value.")

        # Check attributes against table_data
        if settings["increment_revision"]:

            # Extract all unique REV {i} {type} assignments from table_data
            for field in table_data:
                assignment = field.get("Assignment", "")
                if not assignment.startswith("REV "):  # Skip non-REV fields
                    continue

                # Extract the type (e.g., DATE, DESC) from "REV {i} {type}"
                parts = assignment.split()
                if len(parts) < 3 or parts[2] == "REV":  # Skip "REV {i} REV"
                    continue

                field_type = parts[2]  # Extract the type (e.g., DATE, DESC)
                self.used_fields.add(field_type)
                if not settings["attributes"].get(field_type, "").strip():
                    # Add error to the set to ensure uniqueness
                    self.errors.add(
                        f"Attribute '{field_type}' is a required revision field but is missing from revision data."
                    )

            for field_type, value in settings["attributes"].items():
                if value != "" and field_type not in self.used_fields:
                    self.errors.add(
                        f"Setting '{field_type}' is populated but is not included in the table data."
                    )

        # Emit errors if any exist
        if self.errors:
            error_message = '\n'.join(self.errors)  # Combine unique errors into a single string
            self.error_signal.emit(error_message)
            return False

        return True

