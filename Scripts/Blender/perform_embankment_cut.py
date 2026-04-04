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
WALL_THICKNESS = 1 # 0.7=standard, 1=wide
X_OFFSET = 0.0

SUBDIVIDE_CUTS = 1

STANDARD_TUNNEL_CUT_PROFILE = [
    (-3.7 + X_OFFSET - WALL_THICKNESS, -10.0 - WALL_THICKNESS),
    (-3.7 + X_OFFSET - WALL_THICKNESS, 7.9 + WALL_THICKNESS),
    (3.7 + X_OFFSET + WALL_THICKNESS, 7.9 + WALL_THICKNESS),
    (3.7 + X_OFFSET + WALL_THICKNESS, -10.0 - WALL_THICKNESS),
]

WIDE_TUNNEL_CUT_PROFILE_SINGLE = [
    (-4.7 + X_OFFSET - WALL_THICKNESS, -10.0),
    (-4.7 + X_OFFSET - WALL_THICKNESS, 0.0),
    (-6.5 + X_OFFSET - WALL_THICKNESS, 1.5),
    (-3.0 + X_OFFSET - (WALL_THICKNESS / 2), 7.5 + (WALL_THICKNESS / 2)),
    (0.0 + X_OFFSET, 7.5 + (WALL_THICKNESS / 2)),
    (3.0 + X_OFFSET + (WALL_THICKNESS / 2), 7.5 + (WALL_THICKNESS / 2)),
    (6.5 + X_OFFSET + WALL_THICKNESS, 1.5),
    (4.7 + X_OFFSET + WALL_THICKNESS, 0.0),
    (4.7 + X_OFFSET + WALL_THICKNESS, -10.0),
]

WIDE_TUNNEL_CUT_PROFILE_DOUBLE_LEFT = [
    (-2.5 + X_OFFSET, -10.0),
    (-2.5 + X_OFFSET, 7.5 + (WALL_THICKNESS / 2)),
    (0.0 + X_OFFSET, 7.5 + (WALL_THICKNESS / 2)),
    (3.0 + X_OFFSET + (WALL_THICKNESS / 2), 7.5 + (WALL_THICKNESS / 2)),
    (6.5 + X_OFFSET + WALL_THICKNESS, 1.5),
    (4.7 + X_OFFSET + WALL_THICKNESS, 0.0),
    (4.7 + X_OFFSET + WALL_THICKNESS, -10.0),
]

WIDE_TUNNEL_CUT_PROFILE_DOUBLE_RIGHT = [
    (-4.7 + X_OFFSET - WALL_THICKNESS, -10.0),
    (-4.7 + X_OFFSET - WALL_THICKNESS, 0.0),
    (-6.5 + X_OFFSET - WALL_THICKNESS, 1.5),
    (-3.0 + X_OFFSET - (WALL_THICKNESS / 2), 7.5 + (WALL_THICKNESS / 2)),
    (0.0 + X_OFFSET, 7.5 + (WALL_THICKNESS / 2)),
    (2.5 + X_OFFSET, 7.5 + (WALL_THICKNESS / 2)),
    (2.5 + X_OFFSET, -10.0),
]

EMBANKMENT_OBJECT_NAMES = [
    "Carspawner0_1.003_Embankment",
    "Carspawner0_1.003_Embankment.001",
    "Carspawner2_3.003_Embankment",
    "Carspawner2_3.003_Embankment.001",
]

APPLY_CUT_PROFILES = {
    "Underpass1": WIDE_TUNNEL_CUT_PROFILE_DOUBLE_RIGHT,
    "Underpass2": WIDE_TUNNEL_CUT_PROFILE_DOUBLE_LEFT
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


def tangent_at(points, i):
    """
    Computes approximate tangent vector at a point along a polyline.

    Args:
        points (list[Vector]): Ordered list of 3D points.
        i (int): Index of the point to compute tangent for.

    Returns:
        Vector: Normalized tangent vector at the specified point.
    """
    if i == 0:
        return (points[1] - points[0]).normalized()
    elif i == len(points) - 1:
        return (points[-1] - points[-2]).normalized()
    else:
        return (points[i + 1] - points[i - 1]).normalized()


def create_embankment_cutter(curve_obj, cut_profile):
    """
    Generates a cutter mesh along a curve using a specified cross-section profile.

    Args:
        curve_obj (bpy.types.Object): Curve object along which the cutter will be generated.
        cut_profile (list[tuple[float, float]]): 2D profile coordinates defining the cross-section of the cutter.

    Returns:
        bpy.types.Object: The generated cutter object.
    """
    mesh = bpy.data.meshes.new("EmbankmentCutter")
    cutter_obj = bpy.data.objects.new("EmbankmentCutter", mesh)
    bpy.context.collection.objects.link(cutter_obj)
    bm = bmesh.new()
    points_3d = sample_curve(curve_obj)
    vertices_along_spline = []
    for i, point in enumerate(points_3d):
        tangent = tangent_at(points_3d, i)
        z_axis = tangent
        up = Vector((0, 0, 1))
        if abs(z_axis.dot(up)) > 0.999:
            up = Vector((0, 1, 0))
        x_axis = up.cross(z_axis).normalized()
        y_axis = z_axis.cross(x_axis).normalized()
        rotation = Matrix((x_axis, y_axis, z_axis)).transposed()
        row = []
        for point_x, point_y in cut_profile:
            local = Vector((point_x, point_y, 0))
            vert = bm.verts.new(point + rotation @ local)
            row.append(vert)
        vertices_along_spline.append(row)
    bm.verts.ensure_lookup_table()
    for i in range(len(vertices_along_spline) - 1):
        loop1 = vertices_along_spline[i]
        loop2 = vertices_along_spline[i + 1]
        n = len(loop1)
        for j in range(n):
            vert1 = loop1[j]
            vert2 = loop1[(j + 1) % n]
            vert3 = loop2[(j + 1) % n]
            vert4 = loop2[j]
            bm.faces.new([vert1, vert2, vert3, vert4])
    bm.faces.new(vertices_along_spline[0])
    bm.faces.new(list(reversed(vertices_along_spline[-1])))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return cutter_obj


def triangulate_mesh(obj):
    """
    Triangulates all faces of a mesh object in-place.

    Args:
        obj (bpy.types.Object): Mesh object to triangulate.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def apply_boolean_cut(target_obj, cutter_obj):
    """
    Applies a boolean difference modifier to subtract a cutter object from a target object.

    This removes geometry from the target object wherever it overlaps the cutter.

    Args:
        target_obj (bpy.types.Object): The Blender object to be trimmed or cut.
        cutter_obj (bpy.types.Object): The Blender object used as the cutting volume.
    """
    bool_mod = target_obj.modifiers.new("EmbankmentCut", 'BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = cutter_obj
    bool_mod.solver = 'EXACT'
    bool_mod.use_self = True
    bool_mod.use_hole_tolerant = True
    bpy.context.view_layer.objects.active = target_obj
    bpy.ops.object.modifier_apply(modifier="EmbankmentCut")


def perform_embankment_cut():
    """
    Applies boolean cuts to all embankment objects along predefined curves.

    Workflow for each curve and cut profile:
        1. Generate a cutter mesh from the curve and cut profile using `create_embankment_cutter`.
        2. Triangulate the cutter mesh for boolean reliability.
        3. Apply a boolean difference to each embankment object to remove geometry under the cutter.

    Notes:
        - Supports multiple embankment objects and multiple cut profiles per curve.
        - Modifies the embankment objects in-place.
        - Cutters are generated dynamically and applied immediately; they do not persist in the scene.
    """
    for curve_name, cut_profiles in APPLY_CUT_PROFILES.items():
        curve_obj = bpy.data.objects[curve_name]
        if isinstance(cut_profiles[0], tuple) and isinstance(cut_profiles[0][0], (int, float)):
            cut_profiles = [cut_profiles]
        for embankment_obj_name in EMBANKMENT_OBJECT_NAMES:
            for cut_profile in cut_profiles:
                embankment_obj = bpy.data.objects[embankment_obj_name]
                cutter_obj = create_embankment_cutter(curve_obj, cut_profile)
                triangulate_mesh(cutter_obj)
                apply_boolean_cut(embankment_obj, cutter_obj)


perform_embankment_cut()