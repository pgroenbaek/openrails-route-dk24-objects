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

import bpy
import math
from mathutils import Vector, Euler
from pathlib import Path


def get_or_create_child_collection(parent_collection, name):
    """
    Gets an existing child collection by name or creates a new one.

    Args:
        parent_collection (bpy.types.Collection): Parent collection.
        name (str): Name of the child collection.

    Returns:
        bpy.types.Collection: Existing or newly created child collection.
    """
    collection = parent_collection.children.get(name)

    if collection is not None:
        return collection

    collection = bpy.data.collections.new(name)
    parent_collection.children.link(collection)

    return collection


def get_or_create_root_collection(name):
    """
    Gets an existing scene root collection by name or creates a new one.

    Args:
        name (str): Name of the root collection.

    Returns:
        bpy.types.Collection: Existing or newly created scene collection.
    """
    collection = bpy.context.scene.collection.children.get(name)

    if collection is not None:
        return collection

    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)

    return collection


def find_collection_recursive(collection, name):
    """
    Finds a collection by name recursively below a collection.

    Args:
        collection (bpy.types.Collection): Collection to search.
        name (str): Collection name.

    Returns:
        bpy.types.Collection or None: Matching collection if found.
    """
    if collection.name == name:
        return collection

    for child in collection.children:
        result = find_collection_recursive(child, name)

        if result is not None:
            return result

    return None


def remove_collection_tree(collection):
    """
    Removes a collection and its child collections.

    Args:
        collection (bpy.types.Collection): Collection to remove.
    """
    for child in list(collection.children):
        remove_collection_tree(child)

    bpy.data.collections.remove(collection, do_unlink=True)


def import_collection_objects(file_path, collection_name):
    """
    Imports objects belonging to a specific collection tree from a Blender file.

    Only objects belonging to the requested collection or one of its
    descendants are imported.

    Args:
        file_path (str or Path): Path to the source .blend file.
        collection_name (str): Root collection to import.

    Returns:
        list: Imported objects grouped by their source collection path.
    """
    file_path = Path(file_path).resolve()

    if not file_path.exists():
        raise FileNotFoundError(f"Blend file not found: {file_path}")

    imported_objects = []

    with bpy.data.libraries.load(str(file_path), link=False) as (data_from, data_to):
        if collection_name not in data_from.collections:
            raise ValueError(f"Collection '{collection_name}' not found in {file_path}")

        source_collection_names = set(data_from.collections)
        data_to.collections = [collection_name]

    source_root = data_to.collections[0]

    if source_root is None:
        raise RuntimeError(f"Failed to import collection '{collection_name}'")

    def collect_collection(collection, path):
        for obj in collection.objects:
            imported_objects.append((obj, path))

        for child in collection.children:
            child_source_name = child.name

            if child_source_name not in source_collection_names:
                child_source_name = next(
                    name
                    for name in source_collection_names
                    if name == child.name
                    or child.name.startswith(name + ".")
                )

            collect_collection(child, path + [child_source_name])

    collect_collection(source_root, [collection_name])

    return imported_objects, source_root


def build_destination_tree(root_collection, collection_paths):
    """
    Creates or reuses a destination collection tree.

    Args:
        root_collection (bpy.types.Collection): Destination root collection.
        collection_paths (list): Collection paths relative to the imported root.

    Returns:
        dict: Mapping from collection paths to destination collections.
    """
    mapping = {
        (): root_collection
    }

    for path in collection_paths:
        current_collection = root_collection
        current_path = ()

        for name in path:
            current_path = current_path + (name,)

            if current_path not in mapping:
                current_collection = get_or_create_child_collection(current_collection, name)
                mapping[current_path] = current_collection
            else:
                current_collection = mapping[current_path]

    return mapping


def link_imported_objects(imported_objects, destination_root):
    """
    Links imported objects into the matching destination collections.

    Args:
        imported_objects (list): Tuples containing imported objects and their
            source collection paths.
        destination_root (bpy.types.Collection): Destination root collection.
    """
    collection_paths = set()

    for obj, path in imported_objects:
        relative_path = tuple(path[1:])
        collection_paths.add(relative_path)

    collection_mapping = build_destination_tree(destination_root, collection_paths)

    for obj, path in imported_objects:
        relative_path = tuple(path[1:])
        target_collection = collection_mapping[relative_path]

        target_collection.objects.link(obj)


def import_blend_file(file_path, collection_name):
    """
    Imports a collection tree from a Blender file and merges it into the
    existing scene collection tree.

    Only the specified collection and its descendants are imported.

    Args:
        file_path (str or Path): Path to the source .blend file.
        collection_name (str): Root collection to import.

    Returns:
        list: Imported Blender objects.
    """
    imported_objects, source_root = import_collection_objects(file_path, collection_name)

    def rename_collection_tree(collection, suffix):
        collection.name = f"__IMPORT_TEMP__{suffix}"

        for index, child in enumerate(collection.children):
            rename_collection_tree(child, f"{suffix}_{index}")

    rename_collection_tree(source_root, collection_name)

    destination_root = get_or_create_root_collection(collection_name)

    link_imported_objects(imported_objects, destination_root)
    remove_collection_tree(source_root)

    return [obj for obj, path in imported_objects]


def transform_objects(objects, location, rotation, scale):
    """
    Applies translation, rotation, and scale to imported objects.

    Args:
        objects (list): Blender objects to transform.
        location (list or Vector): Translation as [x, y, z].
        rotation (list or Vector): Euler XYZ rotation in radians.
        scale (list or Vector): Scale factors as [x, y, z].
    """
    location = Vector(location)
    rotation = Euler([math.radians(angle) for angle in rotation], "XYZ")
    scale = Vector(scale)

    for obj in objects:
        obj.location += location
        obj.rotation_euler.rotate(rotation)
        obj.scale = Vector((
            obj.scale.x * scale.x,
            obj.scale.y * scale.y,
            obj.scale.z * scale.z
        ))


def perform_operation(params):
    """
    Imports and transforms a collection tree from a Blender file.

    Args:
        params (dict): Operation parameters.

            file_path (str):
                Path to the .blend file. Relative paths are resolved against
                `PROJECT_DIR` in `run_operations.py`.

            collection_name (str):
                Root collection to import. Only this collection and its
                descendants are imported.

            location (list, optional):
                Translation as [x, y, z].

            rotation (list, optional):
                Euler XYZ rotation in radians as [x, y, z].

            scale (list, optional):
                Scale as [x, y, z].

            _project_dir (Path):
                Project root directory supplied by the operation runner.
    """
    project_dir = Path(params["_project_dir"])
    file_path = Path(params["file_path"])

    if not file_path.is_absolute():
        file_path = project_dir / file_path

    collection_name = params["collection_name"]
    location = params.get("location", [0.0, 0.0, 0.0])
    rotation = params.get("rotation", [0.0, 0.0, 0.0])
    scale = params.get("scale", [1.0, 1.0, 1.0])

    print(f"Importing blend file: {file_path}")
    print(f"Collection: {collection_name}")

    objects = import_blend_file(file_path, collection_name)
    transform_objects(objects, location, rotation,scale)

    print(f"Imported {len(objects)} objects.")