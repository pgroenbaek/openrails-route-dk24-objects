#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Copyright (C) 2026 Peter Grønbæk Andersen <peter@grnbk.io>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

# This is a Blender Python script.
#
# Do not run this manually, this script is called by `run_operations.py`,
# which reads the JSON configuration and processes the requested Blender
# operations as they are defined. The `run_operations.py` script can be run
# from the command line with Blender or directly from Blender's scripting
# console by pasting in the script with `CONFIG_FILES` configured.

import os
import io
import sys
import string
import bpy
import itertools
from pathlib import Path


SUPPRESS_EXPORTER_ADDON_PRINTS = True


def apply_filename_replacements(value, replacements):
    """
    Applies a set of string replacements to a value.

    Args:
        value (str): The value to apply replacements to. Non-string values are
            converted to strings.
        replacements (dict[str, str]): A dictionary mapping substrings to their
            replacement values.

    Returns:
        str: The resulting string after all replacements have been applied.
    """
    if not isinstance(value, str):
        value = str(value)
    
    for old, new in replacements.items():
        value = value.replace(old, new)
    
    return value


def resolve_pattern_values(pattern, pattern_variables):
    """
    Resolve a pattern into all possible concrete values.

    Args:
        pattern (str): Pattern containing placeholders such as `{variable}`.
        pattern_variables (dict): Variable definitions containing possible
            values and optional transformation rules.

    Returns:
        list[str]: All fully resolved pattern strings.
    """
    if not pattern_variables:
        return [pattern]

    formatter = string.Formatter()
    variable_names = list(dict.fromkeys(
        field_name
        for _, field_name, _, _ in formatter.parse(pattern)
        if field_name is not None
    ))

    if not variable_names:
        return [pattern]

    variable_value_lists = []

    for variable_name in variable_names:
        variable_config = pattern_variables.get(variable_name)

        if not variable_config:
            raise ValueError(
                f"Pattern variable '{variable_name}' defined in pattern "
                f"'{pattern}' was not found in pattern_variables."
            )

        variable_type = variable_config.get("type", "string")
        filename_replacements = variable_config.get("filename_replacements", {})

        if filename_replacements and variable_type != "string":
            raise ValueError(
                f"Cannot use 'filename_replacements' in variable '{variable_name}' "
                "for variable types other than 'string'."
            )

        values = []

        for value in variable_config["values"]:
            if isinstance(value, (int, float)):
                if variable_type != "number":
                    raise ValueError(f"Invalid value '{value}' for value of type 'number'.")
                
                values.append(value)

            elif isinstance(value, str):
                if variable_type != "string":
                    raise ValueError(f"Invalid value '{value}' for value of type 'string'.")

                resolved_value = apply_filename_replacements(value, filename_replacements,)
                values.append(resolved_value)

            elif isinstance(value, dict):
                number_start = value.get("number_start")
                number_stop = value.get("number_stop")
                number_step = value.get("number_step", 1)

                if number_start is None or number_stop is None:
                    raise ValueError(
                        f"Invalid value expression in variable '{variable_name}', "
                        "missing 'number_start' or 'number_stop'."
                    )

                for number in range(number_start, number_stop + 1, number_step):
                    if "pattern" in value:
                        if variable_type != "string":
                            raise ValueError(
                                f"Invalid value expression in variable '{variable_name}', "
                                "expressions cannot contain 'pattern' unless variable type is 'string'."
                            )

                        resolved_value = value["pattern"].format(number=number)

                        resolved_value = apply_filename_replacements(
                            resolved_value,
                            filename_replacements,
                        )

                        values.append(resolved_value)
                    
                    else:
                        values.append(str(number) if variable_type == "string" else number)

            else:
                raise TypeError(
                    "Unsupported value type for variable "
                    f"'{variable_name}': {type(value).__name__}"
                )

        variable_value_lists.append(values)

    return [
        pattern.format(**dict(zip(variable_names, combination)))
        for combination in itertools.product(*variable_value_lists)
    ]


def set_exporter_texture_name(material_name, texture_name):
    """
    Sets the texture name used for a material with the MSTS/ORTS exporter
    if it is not already set.

    Args:
        material_name (str): Name of the Blender material.
        texture_name (str): Texture name to use for the material.

    Raises:
        ValueError: If the material does not exist.
    """
    material = bpy.data.materials.get(material_name)

    if material is None:
        raise ValueError(f"Material not found: '{material_name}'")

    if hasattr(material, "msts") and hasattr(material.msts, "BaseColorFilepath"):
        material.msts.BaseColorFilepath = texture_name


def export_s_file(file_path, use_dds):
    """
    Exports a shape file using Blender's MSTS exporter.

    Args:
        file_path (str): Destination path for the shape file.
        use_dds (bool): Whether to use ".dds" extension on textures instead of ".ace".
    """
    if hasattr(bpy.context.scene, "msts") and hasattr(bpy.context.scene.msts, "UseDDS"):
        bpy.context.scene.msts.UseDDS = use_dds

    if SUPPRESS_EXPORTER_ADDON_PRINTS:
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            bpy.ops.export.msts_s(filepath=file_path)
        finally:
            sys.stdout = old_stdout
    else:
        bpy.ops.export.msts_s(filepath=file_path)


def perform_operation(params):
    """
    Exports one or more MSTS/ORTS shape files using Blender's MSTS exporter.

    Args:
        params (dict): Export configuration.

    Expected keys:
        - "export_folder" (str): Directory where files are written.
        - "use_dds" (bool): Whether to use `.dds` instead of `.ace` for texture extensions.
        - "shape_filename" (str, optional): Name of a single shape to export.
        - "shape_filename_pattern" (str): Pattern used to generate shape names.
        - "materials" (dict, optional): List of materials and their texture filename/patterns.
        - "pattern_variables" (dict): Configuration of the variables used in e.g. `shape_filename_pattern`.
        - "_project_dir" (Path): Project root directory used to resolve
          relative file paths.
    """
    export_folder = Path(params.get("export_folder"))
    use_dds = params.get("use_dds", False)
    shape_filename = params.get("shape_filename")
    shape_filename_pattern = params.get("shape_filename_pattern")
    materials = params.get("materials")
    pattern_variables = params.get("pattern_variables")
    project_dir = Path(params.get("_project_dir"))

    if export_folder and not os.path.isabs(export_folder):
        export_folder = project_dir / export_folder
    
    if shape_filename_pattern:
        shape_filenames = resolve_pattern_values(shape_filename_pattern, pattern_variables)
    else:
        shape_filenames = [shape_filename]
    
    material_textures = {}

    for material in materials:
        material_name = material.get("material_name")
        texture_filename_pattern = material.get("texture_filename_pattern")
        texture_filename = material.get("texture_filename")

        if not material_name:
            raise ValueError(
                f""
            )
            

        if texture_filename_pattern:
            texture_names = resolve_pattern_values(texture_filename_pattern, pattern_variables)

        elif texture_filename:
            texture_names = [texture_filename] * len(shape_filenames)

        else:
            raise ValueError(
                f""
            )
        
        if len(shape_filenames) != len(texture_names):
            raise ValueError(
                f""
            )

        material_textures[material_name] = texture_names

    if export_folder:
        os.makedirs(export_folder, exist_ok=True)
    
    for idx, shape_filename in enumerate(shape_filenames):
        if not shape_filename.endswith(".s"):
            shape_filename = shape_filename + ".s"
        
        export_path = str(export_folder / shape_filename)

        for material_name in material_textures.keys():
            set_exporter_texture_name(material_name, material_textures[material_name][idx])
        
        export_s_file(export_path, use_dds)

        print(f"Exported S file: '{export_path}'")

