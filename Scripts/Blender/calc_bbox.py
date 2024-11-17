# Calculates the ESD_Bounding_Box parameter for .sd files in Blender 4.2.

import bpy
from bpy import context
import numpy as np

def np_matmul_coords(coords, matrix, space=None):
    M = (space @ matrix @ space.inverted()
         if space else matrix).transposed()
    ones = np.ones((coords.shape[0], 1))
    coords4d = np.hstack((coords, ones))
    return np.dot(coords4d, M)[:,:-1]
    return coords4d[:,:-1]

coords = np.vstack(
    tuple(np_matmul_coords(np.array(o.bound_box), o.matrix_world.copy())
        for o in context.scene.objects if o.type == 'MESH'
    )
)

bfl = coords.min(axis=0)
tbr = coords.max(axis=0)
print("%f %f %f %f %f %f" % (bfl[0], bfl[2], bfl[1], tbr[0], tbr[2], tbr[1]))