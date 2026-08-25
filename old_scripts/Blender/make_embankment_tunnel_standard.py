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


UNDERPASS_CURVE_NAME = "Underpass"
SIDE_CURVE_NAMES = ["RWallCurve1", "RWallCurve2"]

WALL_THICKNESS = 0.7
WALL_U_PER_METER = 0.1
WALL_MATERIAL_NAME = "Concrete"

SAMPLE_INTERVAL = 1.0

TUNNEL_PROFILE = [
    (-3.7, -1.0, 0.0), # x, y, v
    (-3.7 - WALL_THICKNESS, -1.0, 0.07),
    (-3.7 - WALL_THICKNESS, -1.0, 0.0),
    (-3.7 - WALL_THICKNESS, 8 + WALL_THICKNESS, 1.0),
    (-3.7 - WALL_THICKNESS, 8 + WALL_THICKNESS, 0.0),
    (3.7 + WALL_THICKNESS, 8 + WALL_THICKNESS, 1.0),
    (3.7 + WALL_THICKNESS, 8 + WALL_THICKNESS, 1.0),
    (3.7 + WALL_THICKNESS, -1.0, 0.0),
    (3.7 + WALL_THICKNESS, -1.0, 0.07),
    (3.7, -1.0, 0.0),
    (3.7, 7.0, 1.0),
    (3.7, 7.0, 0.03),
    (1.7, 7.65, 0.2),
    (0.0, 7.65, 0.0),
    (-1.7, 7.65, 0.2),
    (-3.7, 7.0, 0.03),
    (-3.7, 7.0, 1.0),
    (-3.7, -1.0, 0.0),
    (-3.7, -1.0, 0.19),
]


def tangent_at(points, i):
    """
    Computes the tangent vector at a point along a polyline.

    Args:
        points (list[Vector]): List of 3D points.
        i (int): Index of the point to calculate tangent for.

    Returns:
        Vector: Normalized tangent vector at the specified point.
    """
    if i == 0:
        return (points[1] - points[0]).normalized()
    elif i == len(points) - 1:
        return (points[-1] - points[-2]).normalized()
    else:
        return (points[i + 1] - points[i - 1]).normalized()


def resample_curve(curve_obj, interval=SAMPLE_INTERVAL):
    """
    Samples a Blender curve at fixed intervals along its length.

    Args:
        curve_obj (bpy.types.Object): Curve object to sample.
        interval (float, optional): Approximate distance between sampled points. Defaults to SAMPLE_INTERVAL.

    Returns:
        list[Vector]: Sampled points along the curve in world coordinates.
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
        segment = points[i] - points[i-1]
        accum_dist += segment.length
        if accum_dist >= interval:
            sampled.append(points[i])
            accum_dist = 0.0
    if sampled[-1] != points[-1]:
        sampled.append(points[-1])
    return sampled


def get_wall_inner_end(curve_obj, underpass_mid):
    """
    Returns the end of a side wall closest to the underpass midpoint.

    Args:
        curve_obj (bpy.types.Object): Side wall curve object.
        underpass_mid (Vector): Midpoint of the underpass curve.

    Returns:
        Vector: Point at the wall end nearest the underpass midpoint.
    """
    spline = curve_obj.data.splines[0]
    if spline.type == 'BEZIER':
        points = [curve_obj.matrix_world @ p.co for p in spline.bezier_points]
    else:
        points = [curve_obj.matrix_world @ Vector(p.co.xyz) for p in spline.points]
    point0 = points[0]
    point1 = points[-1]
    if (point0 - underpass_mid).length < (point1 - underpass_mid).length:
        return point0
    else:
        return point1


def project_point_to_polyline(point, polyline):
    """
    Projects a point onto a polyline and returns the closest point and segment index.

    Args:
        point (Vector): Point to project.
        polyline (list[Vector]): List of points forming the polyline.

    Returns:
        tuple(Vector, int): Closest point on polyline and index of segment start.
    """
    best_dist = 1e9
    best_point = None
    best_index = 0
    for i in range(len(polyline) - 1):
        a = polyline[i]
        b = polyline[i + 1]
        ab = b - a
        t = (point - a).dot(ab) / ab.length_squared
        t = max(0.0, min(1.0, t))
        proj = a + ab * t
        dist = (proj - point).length
        if dist < best_dist:
            best_dist = dist
            best_point = proj
            best_index = i
    return best_point, best_index


def insert_point(polyline, point, index):
    """
    Inserts a point into a polyline after a specified index.

    Args:
        polyline (list[Vector]): Polyline points list.
        point (Vector): Point to insert.
        index (int): Index after which to insert the point.

    Returns:
        int: Index of the inserted point.
    """
    polyline.insert(index + 1, point)
    return index+1


def find_tunnel_segment(underpass_points):
    """
    Determines the underpass segment for tunnel creation based on side walls.

    Args:
        underpass_points (list[Vector]): Points along the underpass curve.

    Returns:
        list[Vector] or None: Points of the segment between side walls, or None if walls missing.
    """
    mid_point = underpass_points[len(underpass_points) // 2]
    wall_points = []
    for name in SIDE_CURVE_NAMES:
        obj = bpy.data.objects.get(name)
        if obj:
            wall_points.append(get_wall_inner_end(obj, mid_point))
    if len(wall_points) != 2:
        print("Missing retaining walls")
        return None
    projected_point1, closest_index1 = project_point_to_polyline(wall_points[0], underpass_points)
    inserted_index1 = insert_point(underpass_points, projected_point1, closest_index1)
    projected_point2, closest_index2 = project_point_to_polyline(wall_points[1], underpass_points)
    inserted_index2 = insert_point(underpass_points, projected_point2, closest_index2)
    start_index = min(inserted_index1, inserted_index2)
    end_index = max(inserted_index1, inserted_index2)
    return underpass_points[start_index:end_index + 2]


def sweep_profile_along_points(points, profile):
    """
    Generates a mesh by sweeping a 2D profile along a 3D point path.

    Args:
        points (list[Vector]): Points along which the profile is swept.
        profile (list[tuple[float, float, float]]): 2D profile coordinates in local space.

    Returns:
        bpy.types.Object: Generated tunnel mesh object.
    """
    mesh = bpy.data.meshes.new("Tunnel")
    obj = bpy.data.objects.new("Tunnel", mesh)
    bpy.context.collection.objects.link(obj)
    material = bpy.data.materials.get(WALL_MATERIAL_NAME)
    if material is None:
        material = bpy.data.materials.new(WALL_MATERIAL_NAME)
    if material.name not in obj.data.materials:
        obj.data.materials.append(material)
    material_index = obj.data.materials.find(material.name)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    rows = []
    running_length = 0.0
    for i, point in enumerate(points):
        if i > 0:
            running_length += (points[i] - points[i - 1]).length
        tangent = tangent_at(points, i)
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
            row.append(vert)
        rows.append(row)
    bm.verts.ensure_lookup_table()
    for i in range(len(rows) - 1):
        loop1 = rows[i]
        loop2 = rows[i + 1]
        segment_length = (points[i + 1] - points[i]).length
        u1 = (running_length - segment_length) * WALL_U_PER_METER
        u2 = running_length * WALL_U_PER_METER
        for j in range(len(loop1) - 1):
            vert1 = loop1[j]
            vert2 = loop2[j]
            vert3 = loop2[j + 1]
            vert4 = loop1[j + 1]
            face = bm.faces.new([vert1, vert2, vert3, vert4])
            face.material_index = material_index
            v1 = profile[j][2]
            v2 = profile[j+1][2]
            loops = face.loops
            loops[0][uv_layer].uv = (u1, v1)
            loops[1][uv_layer].uv = (u2, v1)
            loops[2][uv_layer].uv = (u2, v2)
            loops[3][uv_layer].uv = (u1, v2)
    y_values = [p[1] for p in profile]
    y_min = min(y_values)
    y_max = max(y_values)
    y_range = y_max - y_min if y_max != y_min else 1.0
    start_face = bm.faces.new(rows[0])
    start_face.material_index = material_index
    start_loops = start_face.loops
    for i, loops in enumerate(start_loops):
        point_x, point_y, _ = profile[i]
        u = point_x * WALL_U_PER_METER
        v = (point_y - y_min) / y_range
        loops[uv_layer].uv = (u, v)
    end_face = bm.faces.new(list(reversed(rows[-1])))
    end_face.material_index = material_index
    end_loops = end_face.loops
    for i, loops in enumerate(end_loops):
        point_x, point_y, _ = profile[len(profile) - 1 - i]
        u = point_x * WALL_U_PER_METER
        v = (point_y - y_min) / y_range
        loops[uv_layer].uv = (u, v)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return obj


def build_standard_tunnel():
    """
    Builds a standard tunnel mesh along the underpass curve.

    Notes:
        - Resamples the underpass curve to uniform spacing.
        - Determines segment between side walls.
        - Sweeps the TUNNEL_PROFILE along the segment to generate a mesh.
    """
    underpass = bpy.data.objects[UNDERPASS_CURVE_NAME]
    underpass_points = resample_curve(underpass)
    segment = find_tunnel_segment(underpass_points)
    if not segment:
        print("Tunnel segment not found")
        return
    sweep_profile_along_points(segment, TUNNEL_PROFILE)


build_standard_tunnel()
