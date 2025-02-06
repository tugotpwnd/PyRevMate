from models.increment_revision_model import find_latest_revision_value_and_index

class DrawingSummaryManager:
    def __init__(self):
        """Initialize the DrawingSummaryManager with an empty list to store layout summaries."""
        self.layout_summaries = []

    def add_layout(self, layout_data, updated_data_with_static):
        """
        Process and store relevant table data for a layout.

        Parameters:
        - layout_data: List of dictionaries containing table data for a layout.
        - updated_data_with_static: List of dictionaries containing updated static assignments.
        """
        # Create a lookup dictionary from updated_data_with_static
        static_values = {field["Assignment"]: field["Value"] for field in updated_data_with_static}


        # Replace values in layout_data with static assignments, if available
        updated_layout_data = []
        for field in layout_data:
            updated_field = field.copy()
            if field["Assignment"] in static_values:
                updated_field["Value"] = static_values[field["Assignment"]]
            updated_layout_data.append(updated_field)

        # Extract required fields from updated layout data
        revision = next(
            (field["Value"] for field in updated_layout_data if field.get("Assignment") == "REVISION"), None
        )
        drawing_number = next(
            (field["Value"] for field in updated_layout_data if field.get("Assignment") == "DWG No."), None
        )
        drawing_titles = [
            field["Value"]
            for field in updated_layout_data
            if field.get("Assignment") in ["DWG TITLE 1", "DWG TITLE 2", "DWG TITLE 3", "DWG TITLE 4"]
        ]
        concatenated_title = " - ".join(filter(None, drawing_titles))

        rev, index = find_latest_revision_value_and_index(layout_data)
        revision_desc = next(
            (field["Value"] for field in updated_layout_data if field.get("Assignment") == f"REV {index} DESC"), None
        )

        # Add to the summaries list
        self.layout_summaries.append({
            "Revision": revision or "N/A",
            "Revision Description": revision_desc or "N/A",
            "Drawing Number": drawing_number or "N/A",
            "Drawing Title": concatenated_title or "N/A"
        })

    def generate_summary(self):
        """
        Generate a complete summary of all processed layouts.

        Returns:
        - A list of dictionaries with layout summaries.
        """
        return self.layout_summaries

    def clear(self):
        """Clears the list of layout summaries"""
        self.layout_summaries.clear()
