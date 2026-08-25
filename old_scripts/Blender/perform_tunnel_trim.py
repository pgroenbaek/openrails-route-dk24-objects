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
import bmesh
from mathutils import Vector, Matrix


SAMPLE_INTERVAL = 1.0
SUBDIVIDE_CUTS = 1

EMBANKMENT_OBJECT_NAMES = [
    "Carspawner0_1.003_Embankment",
    "Carspawner0_1.003_Embankment.001",
    "Carspawner2_3.003_Embankment",
    "Carspawner2_3.003_Embankment.001",
]

TUNNEL_OBJECT_NAMES = {
    "Tunnel"
}


def sample_curve(curve_obj, interval=SAMPLE_INTERVAL):
    """
    Samples points along a Blender curve at approximately fixed distance intervals.

    Args:
        curve_obj (bpy.types.Object): The Blender curve object to sample.
        interval (float, optional): Approximate distance between sampled points. Defaults to SAMPLE_INTERVAL.

    Returns:
        list[Vector]: List of 3D points in world coordinates sampled along the curve.
    """
    curve = curve_obj.data
    spline = curve.splines[0]
    if spline.type == 'BEZIER':
        points = [p.co for p in spline.bezier_points]
    else:
        points = [p.co for p in spline.points]
    points = [curve_obj.matrix_world @ Vector(p.xyz) for p in points]
    sampled = [points[0]]
    accum_dist = 0.0
    for i in range(1, len(points)):
        segment = points[i] - points[i - 1]
        accum_dist += segment.length
        if accum_dist >= interval:
            sampled.append(points[i])
            accum_dist = 0.0
    return sampled


def apply_boolean_cut(target_obj, cutter_obj):
    """
    Applies a boolean intersect modifier to a target object using a cutter object.

    This keeps only the geometry of the target that overlaps with the cutter.

    Args:
        target_obj (bpy.types.Object): The Blender object to be trimmed.
        cutter_obj (bpy.types.Object): The Blender object used as the cutting volume.
    """
    bool_mod = target_obj.modifiers.new("TunnelTrim", 'BOOLEAN')
    bool_mod.operation = 'INTERSECT'
    bool_mod.object = cutter_obj
    bool_mod.solver = 'EXACT'
    bool_mod.use_self = True
    bool_mod.use_hole_tolerant = True
    bpy.context.view_layer.objects.active = target_obj
    bpy.ops.object.modifier_apply(modifier="TunnelTrim")


def perform_tunnel_trim():
    """
    Duplicates tunnel objects and trims each copy to match embankment geometry.

    For every tunnel and embankment pair:
        1. Duplicates the tunnel to preserve the original.
        2. Applies a boolean intersect modifier with the embankment.
        3. Adds the trimmed tunnel copy to the scene.

    Notes:
        - Supports multiple tunnels and multiple embankments.
        - Each trimmed copy is independent, allowing multiple variations to coexist.
    """
    for tunnel_obj_name in TUNNEL_OBJECT_NAMES:
        tunnel_obj = bpy.data.objects[tunnel_obj_name]
        for embankment_obj_name in EMBANKMENT_OBJECT_NAMES:
            embankment_obj = bpy.data.objects[embankment_obj_name]
            tunnel_copy = tunnel_obj.copy()
            tunnel_copy.data = tunnel_obj.data.copy()
            bpy.context.collection.objects.link(tunnel_copy)
            apply_boolean_cut(tunnel_copy, embankment_obj)


perform_tunnel_trim()
