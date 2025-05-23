# Makes a .sd with correct ESD_Bounding_Box set in Blender 4.2 based on the model shape of objects in a collection.

import os
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
    Calculates and returns the bounding box of all mesh objects in a given Blender collection.

    Args:
        collection_name (str): The name of the collection to calculate the bounding box for.

    Returns:
        str: A string with values for the ESD_Bounding_Box parameter.

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
    bbox = f"{round(bfl[0], 4)} {round(bfl[2], 4)} {round(bfl[1], 4)} {round(tbr[0], 4)} {round(tbr[2], 4)} {round(tbr[1], 4)}"
    return bbox


def get_filepath():
    """
    Generate a file path for a `.sd` file based on the current Blender project.

    Returns:
        str: The full path of the `.sd` file derived from the saved `.blend` file.

    Raises:
        ValueError: If the Blender file has not been saved and no filepath is available.
    """
    blend_filepath = context.blend_data.filepath
    if not blend_filepath:
        raise ValueError("No previously saved file name available. Save the .blend file before using this script.")
    filepath = os.path.splitext(blend_filepath)[0] + ".sd"
    return filepath


def get_shape_name():
    """
    Generate a shape name based on the current Blender file's path.

    Returns:
        str: The base path (excluding extension) of the current `.blend` file, used as a shape identifier.

    Raises:
        ValueError: If the Blender file has not been saved and no filepath is available.
    """
    blend_filepath = context.blend_data.filepath
    if not blend_filepath:
        raise ValueError("No previously saved file name available. Save the .blend file before using this script.")
    directory, filename = os.path.split(blend_filepath)
    shape_name = os.path.splitext(filename)[0]
    return shape_name


def export_sd_file(file_path, shape_name, bbox):
    """
    Exports an SD (Shape Definition) file for MSTS/ORTS.

    Args:
        file_path (str): The destination file path for the SD file.
        shape_name (str): The name of the shape to be referenced in the file.
        bbox (str): The bounding box parameter to be specified in the file.
    """
    with open(file_path, 'w') as sd_file:
        sd_file.write('SIMISA@@@@@@@@@@JINX0t1t______\n')
        sd_file.write(f'Shape ( {shape_name}.s\n')
        sd_file.write('\tESD_Detail_Level ( 0 )\n')
        sd_file.write('\tESD_Alternative_Texture ( 0 )\n')
        sd_file.write(f'\tESD_Bounding_Box ( {bbox} )\n')
        sd_file.write(')\n')


collection_name = "MAIN_0150"
filepath = get_filepath()
shape_name = get_shape_name()
bbox = calc_bbox(collection_name)
export_sd_file(filepath, shape_name, bbox)