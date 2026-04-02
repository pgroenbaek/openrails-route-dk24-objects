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
from mathutils import Vector

# TODO: materials + UV mapping

RWALL_EDGE_CURVE = "RWallCurve1"
UNDERPASS_CURVE = "Underpass"

MATERIAL_NAME = "Concrete"
WALL_THICKNESS = 0.6
WALL_U_PER_METER = 0.1
WALL_OFFSET = -0.1


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


def closest_point_xy(target_point, points):
    """
    Finds the closest point in XY plane from a list of points to a target point.

    Args:
        target_point (Vector): Target 3D point.
        points (list[Vector]): List of 3D points to search.

    Returns:
        Vector: Point from the list closest to the target in XY coordinates.
    """
    target_xy = Vector((target_point.x, target_point.y))
    closest = points[0]
    min_dist = (target_xy - Vector((closest.x, closest.y))).length
    for point in points[1:]:
        dist = (target_xy - Vector((point.x, point.y))).length
        if dist < min_dist:
            min_dist = dist
            closest = point
    return closest


def build_concrete_rwall():
    """
    Builds a concrete retaining wall along an edge curve relative to an underpass curve.

    Notes:
        - Uses the edge curve as the wall path and the underpass curve to determine wall height.
        - Creates a mesh with front/back faces and top/bottom faces.
        - Wall thickness is defined by WALL_THICKNESS constant.
    """
    edge_curve = bpy.data.objects[RWALL_EDGE_CURVE]
    under_curve = bpy.data.objects[UNDERPASS_CURVE]
    edge_points = sample_curve_eval(edge_curve)
    under_points = sample_curve_eval(under_curve)
    mesh = bpy.data.meshes.new("ConcreteRetainingWall")
    obj = bpy.data.objects.new("ConcreteRetainingWall", mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    front_bottom = []
    front_top = []
    back_bottom = []
    back_top = []
    for i, edge_point in enumerate(edge_points):
        under_point = closest_point_xy(edge_point, under_points)
        height = edge_point.z - under_point.z
        if height <= -1.0:
            front_bottom.append(None)
            front_top.append(None)
            back_bottom.append(None)
            back_top.append(None)
            continue
        if i < len(edge_points) - 1:
            direction = (edge_points[i + 1] - edge_points[i]).to_2d().normalized()
        else:
            direction = (edge_points[i] - edge_points[i - 1]).to_2d().normalized()
        perp = Vector((-direction.y, direction.x, 0))
        thickness_offset = perp * (WALL_THICKNESS / 2)
        edge_offset = perp * WALL_OFFSET
        wall_pos = Vector((edge_point.x, edge_point.y, 0)) + edge_offset
        fb = bm.verts.new(Vector((wall_pos.x, wall_pos.y, under_point.z - 1.0)) - thickness_offset)
        bb = bm.verts.new(Vector((wall_pos.x, wall_pos.y, under_point.z - 1.0)) + thickness_offset)
        ft = bm.verts.new(Vector((wall_pos.x, wall_pos.y, edge_point.z)) - thickness_offset)
        bt = bm.verts.new(Vector((wall_pos.x, wall_pos.y, edge_point.z)) + thickness_offset)
        front_bottom.append(fb)
        front_top.append(ft)
        back_bottom.append(bb)
        back_top.append(bt)
    bm.verts.ensure_lookup_table()
    for i in range(len(edge_points) - 1):
        if not front_bottom[i] or not front_bottom[i + 1]:
            continue
        bm.faces.new([front_bottom[i], front_bottom[i + 1], front_top[i + 1], front_top[i]])
        bm.faces.new([back_bottom[i], back_top[i], back_top[i + 1], back_bottom[i + 1]])
        bm.faces.new([front_top[i], front_top[i + 1], back_top[i + 1], back_top[i]])
        bm.faces.new([front_bottom[i], back_bottom[i], back_bottom[i + 1], front_bottom[i + 1]])
    for i, fb in enumerate(front_bottom):
        if fb:
            bm.faces.new([front_bottom[i], front_top[i], back_top[i], back_bottom[i]])
            break
    for i in reversed(range(len(front_bottom))):
        if front_bottom[i]:
            bm.faces.new([front_bottom[i], back_bottom[i], back_top[i], front_top[i]])
            break
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()


build_concrete_rwall()