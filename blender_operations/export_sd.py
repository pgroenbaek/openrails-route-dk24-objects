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
import string
import bpy
import numpy as np
import itertools
from pathlib import Path


DEFAULT_BBOX = "0.0 0.0 0.0 0.0 0.0 0.0"
DEFAULT_BBOX_COLLECTION_NAME = "MAIN"


def np_matmul_coords(coords, matrix):
    """
    Transforms a set of coordinates using a transformation matrix.

    Args:
        coords (numpy.ndarray): An Nx3 array of coordinates to transform.
        matrix (bpy.types.Matrix): The transformation matrix.

    Returns:
        numpy.ndarray: The transformed coordinates as an Nx3 array.
    """
    matrix = matrix.transposed()
    ones = np.ones((coords.shape[0], 1))
    coords4d = np.hstack((coords, ones))
    return np.dot(coords4d, matrix)[:, :-1]


def get_objects_in_collection(collection):
    """
    Recursively retrieves all objects within a Blender collection.

    Args:
        collection (bpy.types.Collection): The collection to search.

    Returns:
        set: Objects contained within the collection and its subcollections.
    """
    objects = set(collection.objects)

    for subcollection in collection.children:
        objects.update(get_objects_in_collection(subcollection))

    return objects


def calc_bbox(collection_name):
    """
    Calculates the bounding box of all mesh objects in a collection.

    Args:
        collection_name (str): Name of the collection to calculate.

    Returns:
        str: Bounding box formatted for ESD_Bounding_Box.

    Raises:
        ValueError: If the collection does not exist or contains no mesh objects.
    """
    collection = bpy.data.collections.get(collection_name)

    if not collection:
        raise ValueError(f"Collection '{collection_name}' not found")

    objects = get_objects_in_collection(collection)
    mesh_objects = [obj for obj in objects if obj.type == "MESH"]

    if not mesh_objects:
        raise ValueError(f"Collection '{collection_name}' contains no mesh objects")

    coords = np.vstack(tuple(
        np_matmul_coords(np.array(obj.bound_box), obj.matrix_world.copy())
        for obj in mesh_objects
    ))

    bottom_front_left = coords.min(axis=0)
    top_back_right = coords.max(axis=0)

    return (
        f"{round(bottom_front_left[0], 4)} "
        f"{round(bottom_front_left[2], 4)} "
        f"{round(bottom_front_left[1], 4)} "
        f"{round(top_back_right[0], 4)} "
        f"{round(top_back_right[2], 4)} "
        f"{round(top_back_right[1], 4)}"
    )


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


def export_sd_file(file_path, shape_name, bbox):
    """
    Exports a shape definition file for MSTS/ORTS.

    Args:
        file_path (str): Destination path for the SD file.
        shape_name (str): Shape name referenced by the SD file.
        bbox (str): Bounding box value for ESD_Bounding_Box.
    """
    with open(file_path, "w", encoding="utf-8") as sd_file:
        sd_file.write("SIMISA@@@@@@@@@@JINX0t1t______\n")

        if shape_name.endswith(".s"):
            sd_file.write(f"Shape ( {shape_name}\n")
        else:
            sd_file.write(f"Shape ( {shape_name}.s\n")
        
        sd_file.write("\tESD_Detail_Level ( 0 )\n")
        sd_file.write("\tESD_Alternative_Texture ( 0 )\n")
        sd_file.write(f"\tESD_Bounding_Box ( {bbox} )\n")
        sd_file.write(")\n")


def perform_operation(params):
    """
    Exports one or more MSTS/ORTS shape definition files.

    Args:
        params (dict): Export configuration.

    Expected keys:
        - "export_folder" (str): Path for a single SD file.
        - "shape_filename" (str): Shape name for a single export, not used when
          specifying `shape_filename_pattern`.
        - "shape_filename_pattern" (str, optional): Pattern for generated shape names.
        - "bbox" (str, optional): Bounding box to use, defaults to bounds of collection "MAIN".
        - "bbox_collection_name" (str, optional): Collection used for calculating
          the bounding box, defaults to "MAIN".
        - "_project_dir" (Path): Project root directory used to resolve
          relative file paths.
    """
    export_folder = Path(params.get("export_folder"))
    shape_filename = params.get("shape_filename")
    shape_filename_pattern = params.get("shape_filename_pattern")
    bbox = params.get("bbox")
    bbox_collection_name = params.get("bbox_collection_name")
    pattern_variables = params.get("pattern_variables")
    project_dir = Path(params.get("_project_dir"))

    if export_folder and not os.path.isabs(export_folder):
        export_folder = project_dir / export_folder
    
    if shape_filename_pattern:
        shape_filenames = resolve_pattern_values(shape_filename_pattern, pattern_variables)
    else:
        shape_filenames = [shape_filename]

    if export_folder:
        os.makedirs(export_folder, exist_ok=True)
    
    if bbox is None:
        try:
            if bbox_collection_name is not None:
                bbox = calc_bbox(bbox_collection_name)
            else:
                bbox = calc_bbox(DEFAULT_BBOX_COLLECTION_NAME)
        
        except ValueError:
            bbox = DEFAULT_BBOX

    for shape_filename in shape_filenames:
        if not shape_filename.endswith(".s"):
            shape_filename = shape_filename + ".s"

        export_path = export_folder / shape_filename.replace(".s", ".sd")

        export_sd_file(export_path, shape_filename, bbox)

        print(f"Exported SD file: '{export_path}'")
