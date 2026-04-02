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


CURVE_NAME = "RailingCurve3"

START_POST_OFFSET = -0.15
END_POST_OFFSET = -0.15
X_OFFSET = 0.25

POST_LENGTH = 0.1
VERTICAL_POSTS = True

POST_U_VALUE_START = 0.2421875
POST_U_VALUE_END = 0.25390625
POST_MATERIAL_NAME = "Railing"
RAILING_U_PER_METER = 0.2
RAILING_MATERIAL_NAME = "Railing"

RAILING_PROFILE = [
    (X_OFFSET, 0.0, 0.5), # x, y, v
    (X_OFFSET, 1.0, 0.734375),
    (-0.05 + X_OFFSET, 1.0, 0.724609375),
    (-0.1 + X_OFFSET, 1.0, 0.734375),
    (-0.1 + X_OFFSET, 0.0, 0.5)
]

POST_PROFILE = [
    (X_OFFSET, 0.0, 0.5),
    (X_OFFSET, 1.0, 0.734375),
    (-0.05 + X_OFFSET, 1.0, 0.724609375),
    (-0.1 + X_OFFSET, 1.0, 0.734375),
    (-0.1 + X_OFFSET, 0.0, 0.5)
]


def sample_curve_eval(curve_obj):
    """
    Samples the 3D points along a Blender curve object.

    Args:
        curve_obj (bpy.types.Object): Curve object to sample.

    Returns:
        list[Vector]: List of 3D points along the evaluated curve.
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = curve_obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    points = [eval_obj.matrix_world @ v.co for v in mesh.vertices]
    eval_obj.to_mesh_clear()
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


def adjust_points_with_offset(points, start_offset=0.0, end_offset=0.0):
    """Adjust points along a polyline by applying offsets at the start and end.

    Args:
        points (list): Sequence of points representing the polyline.
        start_offset (float): Offset applied at the start of the polyline.
        end_offset (float): Offset applied at the end of the polyline.

    Returns:
        list: A new list of points with the offsets applied.
    """
    if len(points) < 2:
        return points
    points_new = points.copy()
    current_offset = start_offset
    point_index = 0
    while current_offset != 0 and point_index < len(points_new) - 1:
        segment_vector = points_new[point_index + 1] - points_new[point_index]
        segment_length = segment_vector.length
        if current_offset > 0:
            points_new.insert(0, points_new[0] - segment_vector.normalized() * current_offset)
            current_offset = 0
        else:
            if abs(current_offset) < segment_length:
                points_new[point_index] = points_new[point_index] + segment_vector.normalized() * abs(current_offset)
                current_offset = 0
            else:
                current_offset += segment_length
                point_index += 1
    points_new = points_new[point_index:]
    current_offset = end_offset
    point_index = len(points_new) - 1
    while current_offset != 0 and point_index > 0:
        segment_vector = points_new[point_index] - points_new[point_index - 1]
        segment_length = segment_vector.length
        if current_offset > 0:
            points_new.append(points_new[-1] + segment_vector.normalized() * current_offset)
            current_offset = 0
        else:
            if abs(current_offset) < segment_length:
                points_new[point_index] = points_new[point_index] - segment_vector.normalized() * abs(current_offset)
                current_offset = 0
            else:
                current_offset += segment_length
                point_index -= 1
    points_new = points_new[:point_index + 1]
    return points_new


def create_profile_mesh(name, profile, points, start_offset=0.0, end_offset=0.0):
    """
    Creates a mesh by extruding a 2D profile along a series of points.

    Args:
        name (str): Name of the new mesh object.
        profile (list[tuple[float, float, float]]): 2D profile coordinates to extrude along points.
        points (list[Vector]): Points along which the profile is extruded.
        start_offset (float, optional): Offset applied to the first point along tangent. Defaults to 0.0.
        end_offset (float, optional): Offset applied to the last point along tangent. Defaults to 0.0.

    Returns:
        bpy.types.Object: The generated mesh object.
    """
    is_post = True if "Post" in name else False
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    material_name = POST_MATERIAL_NAME if is_post else RAILING_MATERIAL_NAME
    material = bpy.data.materials.get(material_name)
    if material is None:
        material = bpy.data.materials.new(material_name)
    if material.name not in obj.data.materials:
        obj.data.materials.append(material)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    image_node = None
    for node in nodes:
        if node.type == 'TEX_IMAGE':
            image_node = node
            break
    if image_node and bsdf:
        links.new(image_node.outputs["Color"], bsdf.inputs["Base Color"])
        links.new(image_node.outputs["Alpha"], bsdf.inputs["Alpha"])
    material.blend_method = 'BLEND'
    material.shadow_method = 'CLIP'
    material_index = obj.data.materials.find(material.name)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
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
        if VERTICAL_POSTS:
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
    running_length = 0.0
    for i in range(len(rows) - 1):
        loop1 = rows[i]
        loop2 = rows[i + 1]
        if is_post:
            u_start = POST_U_VALUE_START
            u_end = POST_U_VALUE_END
        else:
            segment_length = (points[i + 1] - points[i]).length
            u_start = running_length * RAILING_U_PER_METER
            u_end = (running_length + segment_length) * RAILING_U_PER_METER
            running_length += segment_length
        for j in range(len(loop1) - 1):
            vert1 = loop1[j]
            vert2 = loop2[j]
            vert3 = loop2[j + 1]
            vert4 = loop1[j + 1]
            face = bm.faces.new([vert1, vert2, vert3, vert4])
            face.material_index = material_index
            loops = face.loops
            v1 = profile[j][1]
            v2 = profile[j + 1][1]
            loops[0][uv_layer].uv = (u_start, profile[j][2])
            loops[1][uv_layer].uv = (u_end, profile[j][2])
            loops[2][uv_layer].uv = (u_end, profile[j + 1][2])
            loops[3][uv_layer].uv = (u_start, profile[j + 1][2])
    start_face = bm.faces.new(rows[0])
    start_face.material_index = material_index
    loops = start_face.loops
    for i, loop in enumerate(loops):
        loop[uv_layer].uv = (POST_U_VALUE_START, profile[i][2])
    end_face = bm.faces.new(list(reversed(rows[-1])))
    end_face.material_index = material_index
    loops = end_face.loops
    for i, loop in enumerate(loops):
        profile_index = len(profile) - 1 - i
        loop[uv_layer].uv = (POST_U_VALUE_END, profile[profile_index][2])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return obj


def build_rwall_railing():
    """
    Builds a 3D railing along a curve with aligned start and end posts.

    Notes:
        - Creates a continuous railing mesh along CURVE_NAME.
        - Adds start and end posts that sit together with the railing endpoints.
        - `START_POST_OFFSET` and `END_POST_OFFSET` extend or shrink the railing at the curve ends.
    """
    curve_obj = bpy.data.objects.get(CURVE_NAME)
    points = sample_curve_eval(curve_obj)
    points_railing = adjust_points_with_offset(points, start_offset=START_POST_OFFSET, end_offset=END_POST_OFFSET)
    create_profile_mesh(
        f"{CURVE_NAME}_Railing",
        RAILING_PROFILE,
        points_railing
    )
    start_tangent = tangent_at(points_railing, 0)
    start_post_points = [
        points_railing[0] - start_tangent * POST_LENGTH,
        points_railing[0]
    ]
    create_profile_mesh(
        f"{CURVE_NAME}_StartPost",
        POST_PROFILE,
        start_post_points
    )
    end_tangent = tangent_at(points_railing, len(points_railing) - 1)
    end_post_points = [
        points_railing[-1],
        points_railing[-1] + end_tangent * POST_LENGTH
    ]
    create_profile_mesh(
        f"{CURVE_NAME}_EndPost",
        POST_PROFILE,
        end_post_points
    )

build_rwall_railing()