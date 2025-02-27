# Calculate the ESD_Bounding_Box parameter for .sd files in Blender 4.2 based on the model shape of objects in a collection.

import bpy
from bpy import context
import numpy as np

def np_matmul_coords(coords, matrix, space=None):
    M = (space @ matrix @ space.inverted()
         if space else matrix).transposed()
    ones = np.ones((coords.shape[0], 1))
    coords4d = np.hstack((coords, ones))
    return np.dot(coords4d, M)[:,:-1]


def get_objects_in_collection(collection):
    objects = set(collection.objects)
    for subcollection in collection.children:
        objects.update(get_objects_in_collection(subcollection))
    return objects


def calc_bbox(collection_name):
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
    return bfl, tbr


bfl, tbr = calc_bbox("MAIN_0400")
print("ESD_Bounding_Box ( %f %f %f %f %f %f )" % (bfl[0], bfl[2], bfl[1], tbr[0], tbr[2], tbr[1]))