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
        seg_len = (end - start).length
        if seg_len == 0:
            continue
        num = max(int(seg_len / step), 1)
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


def create_face(bm, verts):
    """
    Safely creates a quad or polygon face in a BMesh.

    Args:
        bm (bmesh.types.BMesh): BMesh to add the face to.
        verts (list[bmesh.types.BMVert]): Ordered vertices defining the face.
    """
    try:
        bm.faces.new(verts)
    except ValueError:
        pass


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
    for i, pt in enumerate(points):
        tangent = tangent_at(points, i)
        offset_vec = Vector((0, 0, 0))
        if i == 0 and start_offset != 0.0:
            offset_vec = -tangent.normalized() * start_offset
        elif i == len(points) - 1 and end_offset != 0.0:
            offset_vec = tangent.normalized() * end_offset
        pt_offset = pt + offset_vec
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
        rot = Matrix((x_axis, y_axis, z_axis)).transposed()
        for px, py, _ in profile:
            vert = bm.verts.new(pt_offset + rot @ Vector((px, 0, py)))
            row.append(vert)
        rows.append(row)
    bm.verts.ensure_lookup_table()
    for i in range(len(rows) - 1):
        loop1, loop2 = rows[i], rows[i + 1]
        for j in range(len(loop1) - 1):
            create_face(bm, [loop1[j], loop2[j], loop2[j+1], loop1[j+1]])
    create_face(bm, rows[0])
    create_face(bm, list(reversed(rows[-1])))
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
    points = sample_curve(curve_obj, step=POST_LENGTH/4)
    post_positions = [points[0]]
    acc = 0
    for i in range(1, len(points)):
        acc += (points[i] - points[i - 1]).length
        if acc >= MAX_POST_SPACING:
            post_positions.append(points[i])
            acc = 0
    if post_positions[-1] != points[-1]:
        post_positions.append(points[-1])
    post_indices = []
    for p in post_positions:
        min_dist = float('inf')
        min_i = 0
        for i, pt in enumerate(points):
            d = (pt - p).length
            if d < min_dist:
                min_dist = d
                min_i = i
        post_indices.append(min_i)
    last_idx = post_indices[-1]
    if last_idx == len(points) - 1:
        tangent = tangent_at(points, last_idx)
        new_pt = points[last_idx] + tangent * POST_LENGTH
        points.append(new_pt)
        points[-1] = points[-1] - tangent * POST_LENGTH
        points[-2] = points[-2] - tangent * POST_LENGTH
        points[-3] = points[-3] - tangent * POST_LENGTH
    for i in range(len(post_indices)-1):
        start_idx = post_indices[i]
        end_idx = start_idx + int(POST_LENGTH / (points[1] - points[0]).length)
        end_idx = min(end_idx, post_indices[i + 1])
        post_pts = [points[start_idx], points[end_idx]]
        create_profile_mesh(
            f"{CURVE_NAME}_Post{i}",
            POST_PROFILE,
            post_pts,
            vertical=VERTICAL_POSTS,
            start_offset=START_OFFSET if i == 0 else 0.0,
            end_offset=-START_OFFSET if i == 0 else 0.0
        )
        rail_pts = [points[end_idx], points[post_indices[i + 1]]]
        if len(rail_pts) >= 2:
            create_profile_mesh(
                f"{CURVE_NAME}_Rail{i}",
                RAILING_PROFILE,
                rail_pts,
                vertical=VERTICAL_POSTS,
                start_offset=START_OFFSET if i == 0 else 0.0,
                end_offset=END_OFFSET if i == len(post_indices) - 2 else 0.0
            )
    create_profile_mesh(
        f"{CURVE_NAME}_PostEnd",
        POST_PROFILE,
        points[post_indices[-1]:post_indices[-1] + 2],
        vertical=VERTICAL_POSTS,
        start_offset=-END_OFFSET,
        end_offset=END_OFFSET
    )


build_rwall_fence()
