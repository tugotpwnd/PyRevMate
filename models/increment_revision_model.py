def find_latest_revision_value_and_index(table_data):
    """
    Determine the value of the highest REV {i} REV field with data and its index.

    Parameters:
    - table_data: A list of dictionaries containing table data.

    Returns:
    - A tuple (latest_revision_value, latest_revision_index), or (None, None) if no REV fields have data.
    """


    revision_fields = get_revision_fields()

    latest_revision_value = None
    latest_revision_index = None
    max_revisions = find_max_revisions(table_data)
    for i in range(1, max_revisions + 1):

        # Check if any field for this revision index has data
        has_data = any(
            field.get("Assignment") == template.format(i=i) and field.get("Value")
            for field in table_data
            for template in revision_fields
        )

        if not has_data:
            break  # Stop checking once we find a revision with no data

        # Find the specific "REV {i} REV" field value
        rev_field = next(
            (
                field.get("Value") for field in table_data
                if field.get("Assignment") == f"REV {i} REV" and field.get("Value")
            ),
            None
        )

        if rev_field:
            latest_revision_value = rev_field
            latest_revision_index = i

    return latest_revision_value, latest_revision_index




def is_all_revisions_filled(table_data):
    """
    Check if all revisions in the table data have at least one field filled.

    Parameters:
    - table_data: A list of dictionaries containing table data.

    Returns:
    - True if all revisions (up to the highest revision index found in the table)
      have at least one field filled; False otherwise.
    """

    revision_fields = get_revision_fields()
    max_revisions = find_max_revisions(table_data)
    for i in range(1, max_revisions + 1):

        # Check if any field for this revision index has data
        if not any(
            field.get("Assignment") == template.format(i=i) and field.get("Value")
            for field in table_data
            for template in revision_fields
        ):
            return False  # At least one revision is missing data

    return True  # All revisions are filled


def shift_revisions_down(table_data, layout_name):
    """
    Shift all revision-related fields down by one revision index, including dynamic Tag updates.

    Parameters:
    - table_data: A list of dictionaries containing table data.

    Returns:
    - Updated table data with the lowest revision removed and all revisions shifted down.
    """
    revision_fields = get_revision_fields()
    max_revisions = find_max_revisions(table_data)
    # Build a mapping from revision index to its data
    revision_mapping = {i: {} for i in range(1, max_revisions + 1)}

    # Populate the revision mapping with data from table_data
    for field in table_data:
        assignment = field.get("Assignment", "")
        for i in range(1, max_revisions + 1):
            template = [template.format(i=i) for template in revision_fields]
            if assignment in template:
                revision_mapping[i][assignment] = {"Value": field["Value"], "Tag": field["Tag"]}
                break

    # Shift revisions down: REV 2 becomes REV 1, REV 3 becomes REV 2, etc.
    for i in range(1, max_revisions):
        revision_mapping[i] = revision_mapping[i + 1]

    # Clear the last revision as it is now undefined
    revision_mapping[max_revisions] = {}

    # Construct the updated table_data from revision_mapping
    updated_table_data = []
    for i in range(1, max_revisions + 1):
        for assignment, field_data in revision_mapping[i].items():
            # Update the assignment for the new revision index
            new_assignment = assignment.replace(f"REV {i + 1}", f"REV {i}")
            # Update the tag dynamically based on the revision index
            new_tag = field_data["Tag"].replace(f"{i + 1}", f"{i}")
            # Append the updated field
            updated_table_data.append({
                "Tag": new_tag,
                "Value": field_data["Value"],
                "Assignment": new_assignment,
                'StaticValue': '',
                "Layout": layout_name
            })

    # Add empty fields for the new highest revision index if they exist in the original table_data
    for template in revision_fields:
        assignment = template.format(i=max_revisions)
        # Check if the assignment exists in the original table_data
        tag = next(
            (field["Tag"] for field in table_data if field.get("Assignment") == assignment),
            None  # Return None if not found
        )
        if tag:  # Only add if the Tag exists
            updated_table_data.append({
                "Tag": tag,
                "Value": "",
                "Assignment": assignment,
                "StaticValue": '',
                "Layout": layout_name
            })

    # Check and add the "REVISION" field if it exists
    revision_field = next(
        (field for field in table_data if field.get("Assignment") == "REVISION"),
        None  # Return None if not found
    )
    if revision_field:
        updated_table_data.append({
            "Tag": revision_field["Tag"],
            "Value": "",
            "Assignment": "REVISION",
            "StaticValue": revision_field.get("StaticValue", ''),
            "Layout": layout_name
        })

    return updated_table_data


def modify_table_data_to_increment_revision(revision_type, hardset_revision, attributes, table_data, layout_name):
    """
    Modify the table data to increment the revision based on inputs and settings.

    Parameters:
    - revision_type: The type of revision ("Alphabetical", "Numerical", or "Hardset").
    - hardset_revision: The value to set for a hardset revision.
    - attributes: A dictionary of text input values with labels as keys.
    - table_data: A list of dictionaries containing the table data.

    Returns:
    - A list of updated dictionaries from `table_data` with the updates applied.
      Returns only the parts of `table_data` that have been updated.
      If revisions are shifted, returns all shifted data plus the new revision data.
      If not shifted, returns only the new revision data fields.
    """
    # Check if all revisions in the table are filled
    table_filled = is_all_revisions_filled(table_data)

    # Find the value and index of the latest revision in the table
    revision_value, revision_index = find_latest_revision_value_and_index(table_data)

    # Initialize a list to store the updated table data
    updated_table_data = []

    # Initialize a variable to hold shifted table data (if applicable)
    shifted_table_data = None

    # Determine if we need to shift revisions down
    if table_filled:
        # If all revisions are filled, shift the revisions down
        shifted_table_data = shift_revisions_down(table_data, layout_name)
        # Add all shifted data to the updated table data
        updated_table_data.extend(shifted_table_data)
        # The new revision index remains the same
        new_revision_index = revision_index
    else:
        # If the table is not completely filled, increment the revision index
        new_revision_index = revision_index + 1

    new_revision_value = determine_new_revision_value(
        revision_type=revision_type,
        revision_value=revision_value,
        hardset_revision=hardset_revision
    )

    # Decide which table data to use as the base for updates
    target_table_data = shifted_table_data if table_filled else table_data

    # Update fields from attributes
    for label, text in attributes.items():
        if text.strip():  # Process only non-empty inputs
            assignment_key = f"REV {new_revision_index} {label.upper()}"
            update_field_value(
                target_table_data,
                updated_table_data,
                assignment_key,
                text,
            )

    # Ensure the new revision field is added or updated
    revision_field_key = f"REV {new_revision_index} REV"
    update_field_value(
        target_table_data,
        updated_table_data,
        revision_field_key,
        new_revision_value,
    )

    # Check for and update the "REVISION" assignment field, if it exists
    update_field_value(
        target_table_data,
        updated_table_data,
        "REVISION",
        new_revision_value,
        raise_error=False,  # Do not raise an error if this field does not exist
    )

    # Return the accumulated updates
    return updated_table_data

def find_max_revisions(table_data):
    # Determine the highest revision index (i) present in the table data
    max_revisions = 0
    for field in table_data:
        assignment = field.get("Assignment", "")
        if assignment.startswith("REV ") and "REV" in assignment:
            try:
                index = int(assignment.split(" ")[1])
                max_revisions = max(max_revisions, index)
            except ValueError:
                continue
    return max_revisions

def get_revision_fields():
    """
    Returns the list of revision field templates.
    """
    return [
        "REV {i} REV", "REV {i} DATE", "REV {i} DESC", "REV {i} DESIGNER",
        "REV {i} DRAFTED", "REV {i} CHECKED", "REV {i} RPEQ",
        "REV {i} RPEQSIGN", "REV {i} COMPANY"
    ]

def determine_new_revision_value(revision_type, revision_value=None, hardset_revision=None):
    """
    Determine the value for the new revision based on the revision type.

    Parameters:
    - revision_type: The type of revision ("Alphabetical", "Numerical", or "Hardset").
    - revision_value: The current revision value (optional).
    - hardset_revision: The hardset revision value (required for "Hardset" type).

    Returns:
    - The new revision value.

    Raises:
    - ValueError if the revision type is unknown or if a hardset revision value is not provided.
    """
    if revision_type == "Alphabetical":
        if revision_value and revision_value.isdigit():
            # Start from "A" if the latest revision is numeric
            return "A"
        # Increment the alphabetical revision
        return chr(ord(revision_value.upper()) + 1) if revision_value else "A"
    elif revision_type == "Numerical":
        if revision_value and revision_value.isalpha():
            # Start from "0" if the latest revision is alphabetical
            return "0"
        # Increment the numeric revision
        return str(int(revision_value) + 1) if revision_value else "1"
    elif revision_type == "Hardset Revision":
        if not hardset_revision:
            # Raise an error if the hardset value is not provided
            raise ValueError("Hardset revision is not defined.")
        return hardset_revision
    else:
        # Raise an error for unknown revision types
        raise ValueError(f"Unknown revision type: {revision_type}")

def update_field_value(
    target_table_data, updated_table_data, assignment_key, new_value, raise_error=True
):
    """
    Update the value of a specific field in the table data.

    Parameters:
    - target_table_data: The table data to search for the field.
    - updated_table_data: The list of updated fields (to append to if a match is found).
    - assignment_key: The assignment key to search for.
    - new_value: The value to set for the matching field.
    - raise_error: Whether to raise an error if the field is not found.

    Returns:
    - None. Updates `updated_table_data` in place.

    Raises:
    - ValueError if the field is not found and `raise_error` is True.
    """
    matching_field = next(
        (field for field in target_table_data if field.get("Assignment") == assignment_key),
        None,
    )
    if matching_field:
        # Update the value of the matching field
        matching_field["Value"] = new_value
        # Append to updated table data if not already present
        if matching_field not in updated_table_data:
            updated_table_data.append(matching_field)
    elif raise_error:
        # Raise an error if the field is not found and raise_error is True
        raise ValueError(f"{assignment_key} does not exist in the table data.")
