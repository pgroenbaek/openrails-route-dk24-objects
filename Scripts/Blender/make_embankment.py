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

# TODO: materials + UV mapping

MAKE_SOLID = False
SAMPLE_INTERVAL = 1.0

EMBANKMENT_PROFILE = [
    (21.3000, -16.7500, 0.5),
    (5.3000, -0.7500, 1.0),
    (4.3000, -0.3700, 1.0),
    (4.3000, -0.3700, 1.0),
    (3.0500, -0.3500, 0.0),
    (-3.0500, -0.3500, 0.0),
    (-4.3000, -0.3700, 1.0),
    (-4.3000, -0.3700, 1.0),
    (-5.3000, -0.7500, 1.0),
    (-21.3000, -16.7500, 0.5),
]

APPLY_EMBANKMENT_PROFILES = {
    "Overpass1": [EMBANKMENT_PROFILE],
    "Overpass2": [EMBANKMENT_PROFILE]
}


def sample_curve(curve_obj, interval=SAMPLE_INTERVAL):
    """
    Samples points along a Blender curve at approximately fixed distance intervals.

    Args:
        curve_obj (bpy.types.Object): Curve object to sample.
        interval (float, optional): Approximate distance between sampled points. Defaults to SAMPLE_INTERVAL.

    Returns:
        list[Vector]: List of sampled 3D points in world coordinates along the curve.
    """
    spline = curve_obj.data.splines[0]
    if spline.type == 'BEZIER':
        points = [p.co for p in spline.bezier_points]
    else:
        points = [p.co for p in spline.points]
    points = [curve_obj.matrix_world @ Vector(p.xyz) for p in points]
    sampled = [points[0]]
    accum_dist = 0.0
    for i in range(1, len(points)):
        seg = points[i] - points[i-1]
        seg_len = seg.length
        accum_dist += seg_len
        if accum_dist >= interval:
            sampled.append(points[i])
            accum_dist = 0.0
    return sampled


def tangent_at(points, i):
    """
    Computes the tangent vector at a point along a polyline of points.

    Args:
        points (list[Vector]): List of 3D points.
        i (int): Index of the point to compute the tangent at.

    Returns:
        Vector: Normalized tangent vector at the specified point.
    """
    if i == 0:
        return (points[1] - points[0]).normalized()
    elif i == len(points)-1:
        return (points[-1] - points[-2]).normalized()
    else:
        return (points[i+1] - points[i-1]).normalized()


def sweep_profile_along_curve(curve_obj, profile):
    """
    Sweeps a 2D embankment profile along a 3D curve to generate a mesh.

    Args:
        curve_obj (bpy.types.Object): Curve object along which the profile is swept.
        profile (list[tuple[float, float, float]]): 2D profile coordinates with optional height.

    Returns:
        bpy.types.Object: Generated embankment mesh object.

    Notes:
        - If MAKE_SOLID is True, caps the ends and connects bottom edges to form a solid mesh.
    """
    mesh = bpy.data.meshes.new(f"{curve_obj.data.name}_Embankment")
    embankment_obj = bpy.data.objects.new(f"{curve_obj.data.name}_Embankment", mesh)
    bpy.context.collection.objects.link(embankment_obj)
    bm = bmesh.new()
    points_3d = sample_curve(curve_obj)
    vertices_along_spline = []
    for i, pt in enumerate(points_3d):
        tangent = tangent_at(points_3d, i)
        z_axis = tangent
        up = Vector((0, 0, 1))
        if abs(z_axis.dot(up)) > 0.999:
            up = Vector((0, 1, 0))
        x_axis = up.cross(z_axis).normalized()
        y_axis = z_axis.cross(x_axis).normalized()
        rot = Matrix((x_axis, y_axis, z_axis)).transposed()
        row = []
        for px, py, v in profile:
            local = Vector((px, py, 0))
            vert = bm.verts.new(pt + rot @ local)
            row.append(vert)
        vertices_along_spline.append(row)
    bm.verts.ensure_lookup_table()
    for i in range(len(vertices_along_spline)-1):
        loop1 = vertices_along_spline[i]
        loop2 = vertices_along_spline[i+1]
        n = len(loop1)
        for j in range(n-1):
            bm.faces.new([loop1[j], loop2[j], loop2[j+1], loop1[j+1]])
    if MAKE_SOLID and len(profile) >= 3:
        bm.faces.new(vertices_along_spline[0])
        bm.faces.new(list(reversed(vertices_along_spline[-1])))
        for i in range(len(vertices_along_spline)-1):
            row1 = vertices_along_spline[i]
            row2 = vertices_along_spline[i+1]
            bottom1_left = min(row1, key=lambda v: v.co.x)
            bottom1_right = max(row1, key=lambda v: v.co.x)
            bottom2_left = min(row2, key=lambda v: v.co.x)
            bottom2_right = max(row2, key=lambda v: v.co.x)
            bm.faces.new([bottom1_left, bottom2_left, bottom2_right, bottom1_right])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return embankment_obj


def build_embankment():
    """
    Builds embankment meshes for all specified curves and profiles.

    Notes:
        - Iterates through APPLY_EMBANKMENT_PROFILES dictionary.
        - For each curve, sweeps each assigned profile along the curve.
        - Converts single tuple profiles into a list of profiles if necessary.
    """
    for curve_name, emb_profiles in APPLY_EMBANKMENT_PROFILES.items():
        curve_obj = bpy.data.objects[curve_name]
        if isinstance(emb_profiles[0], tuple) and isinstance(emb_profiles[0][0], (int, float)):
            emb_profiles = [emb_profiles]
        for emb_profile in emb_profile:
            sweep_profile_along_curve(curve_obj, emb_profile)


build_embankment()
