class CrucialFieldValidator:
    def __init__(self, table_data):
        """
        Initialize the validator with crucial tags extracted from table_data.

        Parameters:
        - table_data: List of dictionaries containing table data.
        """
        self.crucial_tags = self.extract_crucial_tags(table_data)

    @staticmethod
    def extract_crucial_tags(table_data):
        """
        Extract crucial tags from the table data where the assignment is not "VARIABLE".

        Parameters:
        - table_data: List of dictionaries containing table data.

        Returns:
        - A set of crucial tags.
        """
        return {field["Tag"] for field in table_data if field.get("Assignment") != "VARIABLE"}

    def validate(self, extracted_data):
        """
        Validate if the extracted data contains all crucial tags.

        Parameters:
        - extracted_data: List of dictionaries from an AutoCAD file.

        Returns:
        - True if all crucial tags are present, False otherwise.
        """
        extracted_tags = {field["Tag"] for field in extracted_data}
        missing_tags = self.crucial_tags - extracted_tags
        if missing_tags:
            return missing_tags
        return False
