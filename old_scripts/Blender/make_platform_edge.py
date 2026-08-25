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


PLATFORM_CURVE_NAME = "Tommerup, Spor 3"

PLATFORM_EDGE_RIGHT = [
    (4.3, 0.0, 0.0),
    (4.3, 2.133, 1.0),
    (2.66, 2.133, 1.0),
    (2.66, 4.133, 0.5),
    (4.66, 4.133, 0.5),
    (6.33, 4.133, 0.0),
    (9.33, 4.133, 0.0),
    (9.33, 0.0, 0.0),
]

PLATFORM_EDGE_LEFT = [
    (-4.3, 0.0, 0.0),
    (-4.3, 2.133, 1.0),
    (-2.66, 2.133, 1.0),
    (-2.66, 4.133, 0.5),
    (-4.66, 4.133, 0.5),
    (-6.33, 4.133, 0.0),
    (-9.33, 4.133, 0.0),
    (-9.33, 0.0, 0.0),
]

PROFILE = PLATFORM_EDGE_LEFT

TILE_U_PER_METER = 2.0


def tangent_at(points, i):
    """
    Computes a tangent vector along a polyline.

    Args:
        points (list[Vector]): List of spline points.
        i (int): Index of the current point.

    Returns:
        Vector: Normalized tangent direction.
    """
    if i == 0:
        return (points[1] - points[0]).normalized()
    elif i == len(points)-1:
        return (points[-1] - points[-2]).normalized()
    else:
        return (points[i+1] - points[i-1]).normalized()


def sweep_platform_mesh(curve_obj, profile, tile_u_per_meter):
    """
    Generates a spline-based mesh with UV mapping along its length.

    Args:
        curve_obj (bpy.types.Object): Curve defining the sweep path.
        profile (list[tuple]): Cross-section profile coordinates.
        tile_u_per_meter (float): Texture tiling density along the spline.

    Returns:
        bpy.types.Object: Generated spline mesh object.

    Notes:
        - The profile is aligned to the spline tangent.
        - UV coordinates are generated based on cumulative spline distance.
        - V coordinates come from the profile definition.
    """
    spline = curve_obj.data.splines[0]
    mesh = bpy.data.meshes.new("spline_mesh")
    obj = bpy.data.objects.new("SplineObject", mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    vertices_along_spline = []
    v_coords_along_spline = []
    points_3d = [Vector(p.co.xyz) for p in spline.points]
    for i, pt in enumerate(points_3d):
        row = []
        row_v = []
        tangent = tangent_at(points_3d, i)
        z_axis = tangent
        up = Vector((0,0,1))
        if abs(z_axis.dot(up)) > 0.999:
            up = Vector((0,1,0))
        x_axis = up.cross(z_axis).normalized()
        y_axis = z_axis.cross(x_axis).normalized()
        rot = Matrix((x_axis, y_axis, z_axis)).transposed()
        for px, py, v in profile:
            local = Vector((px, py, 0))
            vert = bm.verts.new(pt + rot @ local)
            row.append(vert)
            row_v.append(v)
        vertices_along_spline.append(row)
        v_coords_along_spline.append(row_v)
    bm.verts.ensure_lookup_table()
    for i in range(len(vertices_along_spline)-1):
        loop1 = vertices_along_spline[i]
        loop2 = vertices_along_spline[i+1]
        n = len(loop1)
        for j in range(n-1):
            bm.faces.new([loop1[j], loop2[j], loop2[j+1], loop1[j+1]])
    start_loop = vertices_along_spline[0]
    end_loop = vertices_along_spline[-1]
    bm.faces.new(start_loop)
    bm.faces.new(reversed(end_loop))
    bm.to_mesh(mesh)
    bm.free()
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    uv_layer = mesh.uv_layers.active.data
    cumulative_lengths = [0.0]
    for i in range(1, len(points_3d)):
        seg_len = (points_3d[i] - points_3d[i-1]).length
        cumulative_lengths.append(cumulative_lengths[-1] + seg_len)
    profile_len = len(profile)
    for face in mesh.polygons:
        for loop_idx in face.loop_indices:
            vert_idx = mesh.loops[loop_idx].vertex_index
            profile_idx = vert_idx % profile_len
            spline_idx = vert_idx // profile_len
            v_coord = v_coords_along_spline[spline_idx][profile_idx]
            u_coord = cumulative_lengths[spline_idx] * tile_u_per_meter
            uv_layer[loop_idx].uv = (u_coord, v_coord)
    return obj


def build_platform_edge():
    """
    Main execution function that generates the platform edge mesh.
    """
    curve_obj = bpy.data.objects[PLATFORM_CURVE_NAME]
    sweep_platform_mesh(curve_obj, PROFILE, TILE_U_PER_METER)


build_platform_edge()
