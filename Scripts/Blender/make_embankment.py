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
from enum import Enum, auto

class TileDirection(Enum):
    U = auto()
    V = auto()

X_OFFSET = 0.0
SAMPLE_INTERVAL = 1.0
EMBANKMENT_U_PER_METER = 0.04
TRACKBED_V_PER_METER = 0.1

EMBANKMENT_PROFILE_TRACKSIDE_LEFT = [
    (20.9 + X_OFFSET, -16.3, -0.002), # x, y, texcoord
    (4.9 + X_OFFSET, -0.31, -0.9087),
    (3.9 + X_OFFSET, 0.04, -0.9654),
    (3.3 + X_OFFSET, 0.04, -0.998),
    (3.3 + X_OFFSET, -16.3, -0.998),
]

EMBANKMENT_PROFILE_TRACKSIDE_RIGHT = [
    (-3.3 + X_OFFSET, -16.3, -0.998),
    (-3.3 + X_OFFSET, 0.04, -0.998),
    (-3.9 + X_OFFSET, 0.04, -0.9654),
    (-4.9 + X_OFFSET, -0.31, -0.9087),
    (-20.9 + X_OFFSET, -16.3, -0.002),
]

EMBANKMENT_PROFILE_TRACKBED_SINGLE = [
    (3.3 + X_OFFSET, -16.3, 0.145),
    (3.3 + X_OFFSET, 0.04, 0.145),
    (0.0 + X_OFFSET, 0.068, 0.98),
    (-3.3 + X_OFFSET, 0.04, 0.145),
    (-3.3 + X_OFFSET, -16.3, 0.145),
]

EMBANKMENT_PROFILE_TRACKBED_MULTI_RIGHT = [
    (2.5 + X_OFFSET, -16.3, 0.98),
    (2.5 + X_OFFSET, 0.068, 0.98),
    (-3.3 + X_OFFSET, 0.04, 0.145),
    (-3.3 + X_OFFSET, -16.3, 0.145),
]

EMBANKMENT_PROFILE_TRACKBED_MULTI_LEFT = [
    (3.3 + X_OFFSET, -16.3, 0.145),
    (3.3 + X_OFFSET, 0.04, 0.145),
    (-2.5 + X_OFFSET, 0.068, 0.98),
    (-2.5 + X_OFFSET, -16.3, 0.98),
]

EMBANKMENT_PROFILE_TRACKBED_MULTI_CENTER = [
    (2.5 + X_OFFSET, -16.3, 0.255),
    (2.5 + X_OFFSET, 0.068, 0.255),
    (-2.5 + X_OFFSET, 0.068, 0.98),
    (-2.5 + X_OFFSET, -16.3, 0.98),
]

APPLY_EMBANKMENT_PROFILES = {
    "Overpass1": [ # curve name
        # profile, material name, tiling per meter, tile direction
        (EMBANKMENT_PROFILE_TRACKBED_MULTI_RIGHT, "Trackbed", TRACKBED_V_PER_METER, TileDirection.V),
        (EMBANKMENT_PROFILE_TRACKSIDE_RIGHT, "Embankment", EMBANKMENT_U_PER_METER, TileDirection.U),
    ],
    "Overpass2": [
        (EMBANKMENT_PROFILE_TRACKBED_MULTI_LEFT, "Trackbed", TRACKBED_V_PER_METER, TileDirection.V),
        (EMBANKMENT_PROFILE_TRACKSIDE_LEFT, "Embankment", EMBANKMENT_U_PER_METER, TileDirection.U)
    ]
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
    distances = [0.0]
    accum_dist = 0.0
    total_dist = 0.0
    for i in range(1, len(points)):
        segment = points[i] - points[i - 1]
        accum_dist += segment.length
        total_dist += segment.length
        if accum_dist >= interval:
            sampled.append(points[i])
            distances.append(total_dist)
            accum_dist = 0.0
    return sampled, distances


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
    elif i == len(points) - 1:
        return (points[-1] - points[-2]).normalized()
    else:
        return (points[i + 1] - points[i - 1]).normalized()


def sweep_profile_along_curve(curve_obj, profile, material_name, tile_per_meter, tile_direction):
    """
    Sweeps a 2D embankment profile along a 3D curve to generate a mesh.

    Args:
        curve_obj (bpy.types.Object): Curve object along which the profile is swept.
        profile (list[tuple[float, float, float]]): 2D profile coordinates with optional height.
        material_name (str): Material assigned to the generated mesh.
        tile_per_meter (float): Texture tiling density along the curve.
        tile_direction (TileDirection): UV axis used for tiling along the curve.

    Returns:
        bpy.types.Object: Generated embankment mesh object.
    """
    mesh = bpy.data.meshes.new(f"{curve_obj.data.name}_Embankment")
    embankment_obj = bpy.data.objects.new(f"{curve_obj.data.name}_Embankment", mesh)
    bpy.context.collection.objects.link(embankment_obj)
    material = bpy.data.materials.get(material_name)
    if material is None:
        material = bpy.data.materials.new(material_name)
    if material.name not in embankment_obj.data.materials:
        embankment_obj.data.materials.append(material)
    material_index = embankment_obj.data.materials.find(material.name)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    points_3d, distances = sample_curve(curve_obj)
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
        for point_x, point_y, texcoord in profile:
            local = Vector((point_x, point_y, 0))
            vert = bm.verts.new(point + rotation @ local)
            row.append((vert, texcoord))
        vertices_along_spline.append(row)
    bm.verts.ensure_lookup_table()
    for i in range(len(vertices_along_spline) - 1):
        loop1 = vertices_along_spline[i]
        loop2 = vertices_along_spline[i + 1]
        distance1 = distances[i]
        distance2 = distances[i + 1]
        for j in range(len(loop1) - 1):
            vert1, texcoord1 = loop1[j]
            vert2, texcoord2 = loop1[j + 1]
            vert3, texcoord3 = loop2[j + 1]
            vert4, texcoord4 = loop2[j]
            face = bm.faces.new([vert1, vert4, vert3, vert2])
            face.material_index = material_index
            loops = face.loops
            tiled_texcoord1 = distance1 * tile_per_meter
            tiled_texcoord2 = distance2 * tile_per_meter
            if tile_direction == TileDirection.U:
                loops[0][uv_layer].uv = (tiled_texcoord1, texcoord1)
                loops[1][uv_layer].uv = (tiled_texcoord2, texcoord4)
                loops[2][uv_layer].uv = (tiled_texcoord2, texcoord3)
                loops[3][uv_layer].uv = (tiled_texcoord1, texcoord2)
            else: # TileDirection.V
                loops[0][uv_layer].uv = (texcoord1, tiled_texcoord1)
                loops[1][uv_layer].uv = (texcoord4, tiled_texcoord2)
                loops[2][uv_layer].uv = (texcoord3, tiled_texcoord2)
                loops[3][uv_layer].uv = (texcoord2, tiled_texcoord1)
    if len(profile) >= 3:
        bm.faces.new([vert[0] for vert in vertices_along_spline[0]])
        bm.faces.new(list(reversed([vert[0] for vert in vertices_along_spline[-1]])))
        for i in range(len(vertices_along_spline) - 1):
            row1 = vertices_along_spline[i]
            row2 = vertices_along_spline[i + 1]
            bottom1_left = row1[0][0]
            bottom1_right = row1[-1][0]
            bottom2_left = row2[0][0]
            bottom2_right = row2[-1][0]
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
        for emb_profile, material_name, tile_per_meter, tile_direction in emb_profiles:
            sweep_profile_along_curve(curve_obj, emb_profile, material_name, tile_per_meter, tile_direction)


build_embankment()