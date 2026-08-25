import os
import bpy


EXPORT_PATH = None
MATERIAL_NAME = None


def ensure_directory_exists(path):
    """
    Ensures that a directory exists by creating it if necessary.

    Args:
        path (str): Directory path to check or create.
    """
    os.makedirs(path, exist_ok=True)


def replace_text_in_file(file_path, search_text, replace_text):
    """
    Replaces all occurrences of text in a UTF-16 encoded file.

    Args:
        file_path (str): Path to the file to modify.
        search_text (str): Text to search for.
        replace_text (str): Text to replace it with.
    """
    with open(file_path, "r", encoding="utf-16") as file:
        file_text = file.read()

    file_text = file_text.replace(search_text, replace_text)

    with open(file_path, "w", encoding="utf-16") as file:
        file.write(file_text)


def export_s_file(file_path):
    """
    Exports an S file using Blender's MSTS exporter.

    Args:
        file_path (str): Destination path for the S file.
    """
    bpy.ops.export.msts_s(filepath=file_path)


def sanitize_value(value, replacements):
    """
    Applies configured string replacements to a value.

    Args:
        value (str): Value to sanitize.
        replacements (dict): Mapping of strings to replacement strings.

    Returns:
        str: Sanitized value.
    """
    value = str(value)

    for search, replace in replacements.items():
        value = value.replace(search, replace)

    return value


def build_exports(params):
    """
    Builds the list of exports from the operation parameters.

    Args:
        params (dict): Export configuration.

    Returns:
        list: List of dictionaries containing export variables.
    """
    exports = params.get("exports")

    if exports is not None:
        return exports

    values = params.get("values")

    if values is not None:
        return [{"value": value} for value in values]

    groups = params.get("groups")

    if groups is not None:
        exports = []

        for group in groups:
            prefix = group.get("prefix", "")
            start = group["start"]
            stop = group["stop"]
            step = group.get("step", 1)
            number_format = group.get("number_format", "03d")

            for number in range(start, stop + 1, step):
                value = f"{prefix}-{number:{number_format}}"
                exports.append({"value": value})

        return exports

    raise ValueError("No exports, values, or groups specified.")


def perform_operation(params):
    """
    Exports one or more MSTS/ORTS S files using Blender's MSTS exporter.

    Args:
        params (dict): Export configuration.

    Expected keys include:
        - "export_path" (str): Directory where S files are written.
        - "shape_name" (str, optional): Name of a single shape to export.
        - "exports" (list, optional): Explicit list of export variable dictionaries.
        - "values" (list, optional): List of values used by the filename patterns.
        - "groups" (list, optional): Groups used to generate numbered values.
        - "shape_name_pattern" (str): Pattern used to generate shape names.
        - "texture_name_pattern" (str, optional): Pattern used to generate texture names.
        - "material_name" (str, optional): Material texture filename to replace.
        - "value_replacements" (dict, optional): String replacements applied to values.
    """
    export_path = params.get("export_path", EXPORT_PATH)
    shape_name = params.get("shape_name")
    shape_name_pattern = params.get("shape_name_pattern")
    texture_name_pattern = params.get("texture_name_pattern")
    material_name = params.get("material_name", MATERIAL_NAME)
    replacements = params.get("value_replacements", {})
    project_dir = params.get("_project_dir")

    if export_path and not os.path.isabs(export_path):
        export_path = os.path.join(project_dir, export_path)

    if not export_path:
        raise ValueError("No export_path specified.")

    if shape_name:
        exports = [{"value": shape_name}]
    else:
        exports = build_exports(params)

    ensure_directory_exists(export_path)

    for export in exports:
        values = {
            key: sanitize_value(value, replacements)
            for key, value in export.items()
        }

        if shape_name:
            current_shape_name = shape_name
        else:
            current_shape_name = shape_name_pattern.format(**values)

        texture_name = None

        if texture_name_pattern:
            texture_name = texture_name_pattern.format(**values)

        file_path = os.path.join(export_path, f"{current_shape_name}.s")

        export_s_file(file_path)

        if material_name and texture_name:
            replace_text_in_file(
                file_path,
                f"{material_name}.ace",
                f"{texture_name}.ace"
            )

        print(f"Exported S file: {file_path}")