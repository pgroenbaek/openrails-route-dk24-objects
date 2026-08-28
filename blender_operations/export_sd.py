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
# It is called by `run_operations.py`, which reads the JSON configuration
# and dispatches the requested Blender operations. The `run_operations.py`
# script can also be run directly from Blender's scripting console
# configured with a set of config files and pasting it in.

import os
import bpy
import numpy as np


COLLECTION_NAME = "MAIN_0150"


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

    coords = np.vstack(
        tuple(
            np_matmul_coords(np.array(obj.bound_box), obj.matrix_world.copy())
            for obj in mesh_objects
        )
    )

    bfl = coords.min(axis=0)
    tbr = coords.max(axis=0)

    return f"{round(bfl[0], 4)} {round(bfl[2], 4)} {round(bfl[1], 4)} {round(tbr[0], 4)} {round(tbr[2], 4)} {round(tbr[1], 4)}"


def get_filepath():
    """
    Generates the default SD file path from the current Blender project.

    Returns:
        str: The SD file path.

    Raises:
        ValueError: If the Blender file has not been saved.
    """
    blend_filepath = bpy.data.filepath

    if not blend_filepath:
        raise ValueError("No previously saved file name available.")

    return os.path.splitext(blend_filepath)[0] + ".sd"


def get_shape_name():
    """
    Generates the default shape name from the current Blender filename.

    Returns:
        str: The Blender filename without its extension.

    Raises:
        ValueError: If the Blender file has not been saved.
    """
    blend_filepath = bpy.data.filepath

    if not blend_filepath:
        raise ValueError("No previously saved file name available.")

    filename = os.path.basename(blend_filepath)

    return os.path.splitext(filename)[0]


def export_sd_file(file_path, shape_name, bbox):
    """
    Exports an SD shape definition file for MSTS/ORTS.

    Args:
        file_path (str): Destination path for the SD file.
        shape_name (str): Shape name referenced by the SD file.
        bbox (str): Bounding box for ESD_Bounding_Box.
    """
    with open(file_path, "w", encoding="utf-8") as sd_file:
        sd_file.write("SIMISA@@@@@@@@@@JINX0t1t______\n")
        sd_file.write(f"Shape ( {shape_name}.s\n")
        sd_file.write("\tESD_Detail_Level ( 0 )\n")
        sd_file.write("\tESD_Alternative_Texture ( 0 )\n")
        sd_file.write(f"\tESD_Bounding_Box ( {bbox} )\n")
        sd_file.write(")\n")


def build_exports(params):
    """
    Builds the list of SD exports from the operation parameters.

    Args:
        params (dict): Export configuration.

    Returns:
        list: List of export dictionaries.
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
    Exports one or more MSTS/ORTS SD shape definition files.

    Args:
        params (dict): Export configuration.

    Expected keys include:
        - "file_path" (str, optional): Path for a single SD file.
        - "shape_name" (str, optional): Shape name for a single export.
        - "collection_name" (str, optional): Collection used for the bounding box.
        - "export_path" (str, optional): Directory for generated SD files.
        - "shape_name_pattern" (str, optional): Pattern for generated shape names.
        - "values" (list, optional): Explicit values used by naming patterns.
        - "groups" (list, optional): Numbered groups used to generate values.
        - "exports" (list, optional): Explicit export definitions.
        - "bbox" (str, optional): Explicit bounding box instead of calculating one.
    """
    export_path = params.get("export_path")
    collection_name = params.get("collection_name", COLLECTION_NAME)
    shape_name = params.get("shape_name")
    shape_name_pattern = params.get("shape_name_pattern")
    explicit_file_path = params.get("file_path")
    explicit_bbox = params.get("bbox")
    project_dir = params.get("_project_dir")

    if export_path and not os.path.isabs(export_path):
        export_path = os.path.join(project_dir, export_path)

    if explicit_file_path or shape_name:
        exports = [{
            "shape_name": shape_name or get_shape_name(),
            "file_path": explicit_file_path,
            "collection_name": collection_name
        }]
    else:
        exports = build_exports(params)

    if export_path:
        os.makedirs(export_path, exist_ok=True)

    for export in exports:
        current_collection = export.get("collection_name", collection_name)
        current_shape_name = export.get("shape_name")

        if current_shape_name is None:
            current_shape_name = shape_name_pattern.format(**export)

        file_path = export.get("file_path")

        if file_path is None:
            if not export_path:
                raise ValueError("No export_path specified.")

            file_path = os.path.join(
                export_path,
                f"{current_shape_name}.sd"
            )

        bbox = export.get("bbox", explicit_bbox)

        if bbox is None:
            bbox = calc_bbox(current_collection)

        export_sd_file(file_path, current_shape_name, bbox)

        print(f"Exported SD file: {file_path}")
        print(f"Shape: {current_shape_name}")
        print(f"Bounding box: {bbox}")