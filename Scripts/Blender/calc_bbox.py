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

import bpy
from bpy import context
import numpy as np


def np_matmul_coords(coords, matrix, space=None):
    """
    Transforms a set of coordinates using a transformation matrix.

    Args:
        coords (numpy.ndarray): An Nx3 array of coordinates to be transformed.
        matrix (bpy.types.Matrix): The transformation matrix.
        space (bpy.types.Matrix, optional): An additional space transformation matrix. 
            If provided, the transformation is applied in the given space.

    Returns:
        numpy.ndarray: The transformed coordinates as an Nx3 array.

    Notes:
        - If `space` is provided, the transformation matrix is converted to the 
          corresponding space before application.
        - Uses homogeneous coordinates to perform the transformation.
    """
    M = (space @ matrix @ space.inverted()
         if space else matrix).transposed()
    ones = np.ones((coords.shape[0], 1))
    coords4d = np.hstack((coords, ones))
    return np.dot(coords4d, M)[:,:-1]


def get_objects_in_collection(collection):
    """
    Recursively retrieves all objects within a Blender collection, including those in subcollections.

    Args:
        collection (bpy.types.Collection): The collection to search within.

    Returns:
        set: A set of Blender objects contained within the collection and its subcollections.
    """
    objects = set(collection.objects)
    for subcollection in collection.children:
        objects.update(get_objects_in_collection(subcollection))
    return objects


def calc_bbox(collection_name):
    """
    Calculates and prints the bounding box of all mesh objects in a given Blender collection.

    Args:
        collection_name (str): The name of the collection to calculate the bounding box for.

    Raises:
        ValueError: If the specified collection does not exist.
    """
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        raise ValueError(f"Collection '{collection_name}' not found")
    objects = get_objects_in_collection(collection)
    coords = np.vstack(
        tuple(np_matmul_coords(np.array(o.bound_box), o.matrix_world.copy())
              for o in objects if o.type == 'MESH')
    )
    bfl = coords.min(axis=0)
    tbr = coords.max(axis=0)
    print(f"ESD_Bounding_Box ( {round(bfl[0], 4)} {round(bfl[2], 4)} {round(bfl[1], 4)} {round(tbr[0], 4)} {round(tbr[2], 4)} {round(tbr[1], 4)} )")


collection_name = "MAIN_0150"
calc_bbox(collection_name)