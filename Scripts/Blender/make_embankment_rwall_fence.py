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

CURVE_NAME = "EdgeCurveGuardRail3"

START_OFFSET = -0.15
END_OFFSET = -0.15
MAX_POST_SPACING = 2.0
POST_LENGTH = 0.1
VERTICAL_POSTS = True
X_OFFSET = -0.1

RAILING_PROFILE = [
    (X_OFFSET, 0.0, 0.0),
    (X_OFFSET, 1.0, 0.0),
    (-0.1 + X_OFFSET, 1.0, 0.0),
    (-0.1 + X_OFFSET, 0.0, 0.0),
    (X_OFFSET, 0.0, 0.0),
]

POST_PROFILE = [
    (X_OFFSET, 0.0, 0.0),
    (X_OFFSET, 1.0, 0.0),
    (-0.1 + X_OFFSET, 1.0, 0.0),
    (-0.1 + X_OFFSET, 0.0, 0.0),
    (X_OFFSET, 0.0, 0.0),
]


def sample_curve(curve_obj, step=0.1):
    """
    Samples a Blender curve by evaluating its mesh and interpolating points at fixed steps.

    Args:
        curve_obj (bpy.types.Object): Curve object to sample.
        step (float, optional): Approximate distance between sampled points. Defaults to 0.1.

    Returns:
        list[Vector]: List of 3D points sampled along the curve.
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = curve_obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    verts = [v.co.copy() for v in mesh.vertices]
    eval_obj.to_mesh_clear()
    if len(verts) < 2:
        return []
    points = [verts[0]]
    for i in range(1, len(verts)):
        start, end = verts[i - 1], verts[i]
        segment_length = (end - start).length
        if segment_length == 0:
            continue
        num = max(int(segment_length / step), 1)
        for j in range(1, num + 1):
            points.append(start + (end - start) * (j / num))
    return points


def tangent_at(points, i):
    """
    Computes the approximate tangent vector at a point along a polyline.

    Args:
        points (list[Vector]): List of 3D points.
        i (int): Index of the point to compute tangent for.

    Returns:
        Vector: Normalized tangent vector at the specified index.
    """
    if len(points) < 2:
        return Vector((0, 0, 1))
    if i == 0:
        return (points[1] - points[0]).normalized()
    if i == len(points) - 1:
        return (points[-1] - points[-2]).normalized()
    return (points[i + 1] - points[i - 1]).normalized()


def create_profile_mesh(name, profile, points, vertical=False, start_offset=0.0, end_offset=0.0):
    """
    Creates a mesh by extruding a 2D profile along a series of points.

    Args:
        name (str): Name of the new mesh object.
        profile (list[tuple[float, float, float]]): 2D profile coordinates to extrude along points.
        points (list[Vector]): Points along which the profile is extruded.
        vertical (bool, optional): Align profile vertically if True. Defaults to False.
        start_offset (float, optional): Offset applied to the first point along tangent. Defaults to 0.0.
        end_offset (float, optional): Offset applied to the last point along tangent. Defaults to 0.0.

    Returns:
        bpy.types.Object: The generated mesh object.
    """
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    rows = []
    for i, point in enumerate(points):
        tangent = tangent_at(points, i)
        offset_vector = Vector((0, 0, 0))
        if i == 0 and start_offset != 0.0:
            offset_vector = -tangent.normalized() * start_offset
        elif i == len(points) - 1 and end_offset != 0.0:
            offset_vector = tangent.normalized() * end_offset
        point_offset = point + offset_vector
        row = []
        if vertical:
            z_axis = Vector((0, 0, 1))
            x_axis = tangent.cross(z_axis)
            if x_axis.length == 0:
                x_axis = Vector((1, 0, 0))
            x_axis.normalize()
            y_axis = z_axis.cross(x_axis).normalized()
        else:
            z_axis = Vector((0, 0, 1)) - tangent * Vector((0, 0, 1)).dot(tangent)
            if z_axis.length == 0:
                z_axis = Vector((0, 0, 1))
            z_axis.normalize()
            x_axis = tangent.cross(z_axis).normalized()
            y_axis = z_axis.cross(x_axis).normalized()
        rotation = Matrix((x_axis, y_axis, z_axis)).transposed()
        for point_x, point_y, _ in profile:
            vert = bm.verts.new(point_offset + rotation @ Vector((point_x, 0, point_y)))
            row.append(vert)
        rows.append(row)
    bm.verts.ensure_lookup_table()
    for i in range(len(rows) - 1):
        loop1 = rows[i]
        loop2 = rows[i + 1]
        for j in range(len(loop1) - 1):
            vert1 = loop1[j]
            vert2 = loop2[j]
            vert3 = loop2[j + 1]
            vert4 = loop1[j + 1]
            bm.faces.new([vert1, vert2, vert3, vert4])
    bm.faces.new(rows[0])
    bm.faces.new(list(reversed(rows[-1])))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return obj


def build_rwall_fence():
    """
    Builds a fence along a predefined curve.

    Notes:
        - Samples points along CURVE_NAME and determines post positions based on MAX_POST_SPACING.
        - Creates vertical posts and connecting rail meshes using `create_profile_mesh`.
        - Adjusts start/end offsets and extends last post to maintain consistent spacing.
        - Generates separate mesh objects for each post and rail segment.
    """
    curve_obj = bpy.data.objects.get(CURVE_NAME)
    if not curve_obj:
        print(f"Curve '{CURVE_NAME}' not found")
        return
    points = sample_curve(curve_obj, step=POST_LENGTH / 4)
    post_positions = [points[0]]
    accum_dist = 0
    for i in range(1, len(points)):
        accum_dist += (points[i] - points[i - 1]).length
        if accum_dist >= MAX_POST_SPACING:
            post_positions.append(points[i])
            accum_dist = 0
    if post_positions[-1] != points[-1]:
        post_positions.append(points[-1])
    post_indices = []
    for post_position in post_positions:
        min_dist = float('inf')
        min_i = 0
        for i, point in enumerate(points):
            dist = (point - post_position).length
            if dist < min_dist:
                min_dist = dist
                min_i = i
        post_indices.append(min_i)
    last_idx = post_indices[-1]
    if last_idx == len(points) - 1:
        tangent = tangent_at(points, last_idx)
        new_point = points[last_idx] + tangent * POST_LENGTH
        points.append(new_point)
        points[-1] = points[-1] - tangent * POST_LENGTH
        points[-2] = points[-2] - tangent * POST_LENGTH
        points[-3] = points[-3] - tangent * POST_LENGTH
    for i in range(len(post_indices) - 1):
        start_idx = post_indices[i]
        end_idx = start_idx + int(POST_LENGTH / (points[1] - points[0]).length)
        end_idx = min(end_idx, post_indices[i + 1])
        post_points = [points[start_idx], points[end_idx]]
        create_profile_mesh(
            f"{CURVE_NAME}_Post{i}",
            POST_PROFILE,
            post_points,
            vertical=VERTICAL_POSTS,
            start_offset=START_OFFSET if i == 0 else 0.0,
            end_offset=-START_OFFSET if i == 0 else 0.0
        )
        rail_points = [points[end_idx], points[post_indices[i + 1]]]
        if len(rail_points) >= 2:
            create_profile_mesh(
                f"{CURVE_NAME}_Rail{i}",
                RAILING_PROFILE,
                rail_points,
                vertical=VERTICAL_POSTS,
                start_offset=START_OFFSET if i == 0 else 0.0,
                end_offset=END_OFFSET if i == len(post_indices) - 2 else 0.0
            )
    last_post_points = points[post_indices[-1]:post_indices[-1] + 2]
    create_profile_mesh(
        f"{CURVE_NAME}_PostEnd",
        POST_PROFILE,
        last_post_points,
        vertical=VERTICAL_POSTS,
        start_offset=-END_OFFSET,
        end_offset=END_OFFSET
    )


build_rwall_fence()
