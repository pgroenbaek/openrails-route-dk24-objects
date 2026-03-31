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
import math

# TODO: materials + UV mapping

EDGE_CURVE = "EdgeCurveRWall2"
UNDERPASS_CURVE = "Underpass"

CONCRETE_EDGE_THICKNESS = 0.6
CONCRETE_EDGE_HEIGHT = 0.5

STEEL_ZIGZAG = False
STEEL_ZIGZAG_AMPLITUDE = 0.2
STEEL_STEP_LENGTH = 0.6
STEEL_FLIP_FACES = True

PHASE_SEQUENCE = [2, 0, 2, 1] # 0=left, 1=right, 2=straight


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
    pts = [eval_obj.matrix_world @ v.co for v in mesh.vertices]
    eval_obj.to_mesh_clear()
    return pts


def cumulative_lengths(points):
    """
    Computes cumulative distances along a list of points.

    Args:
        points (list[Vector]): List of 3D points.

    Returns:
        tuple[list[float], float]: Cumulative lengths at each point and total length.
    """
    lengths = [0.0]
    for i in range(1, len(points)):
        lengths.append(lengths[-1] + (points[i] - points[i-1]).length)
    return lengths, lengths[-1]


def sample_by_distance(points, lengths, total_length, dist):
    """
    Samples a point along a polyline at a given distance.

    Args:
        points (list[Vector]): List of 3D points.
        lengths (list[float]): Cumulative lengths along the points.
        total_length (float): Total length of the polyline.
        dist (float): Distance along the polyline to sample.

    Returns:
        Vector: Interpolated 3D point at the specified distance.
    """
    dist = max(0.0, min(dist, total_length))
    for i in range(len(lengths)-1):
        if lengths[i] <= dist <= lengths[i+1]:
            t = (dist - lengths[i])/(lengths[i+1]-lengths[i])
            return points[i].lerp(points[i+1], t)
    return points[-1]


def closest_point_xy(target_pt, points):
    """
    Finds the closest point in XY plane from a list of points to a target point.

    Args:
        target_pt (Vector): Target 3D point.
        points (list[Vector]): List of 3D points to search.

    Returns:
        Vector: Point from the list closest to the target in XY coordinates.
    """
    target_xy = Vector((target_pt.x, target_pt.y))
    closest = points[0]
    min_dist = (target_xy - Vector((closest.x, closest.y))).length
    for p in points[1:]:
        d = (target_xy - Vector((p.x, p.y))).length
        if d < min_dist:
            min_dist = d
            closest = p
    return closest


def build_steel_rwall():
    """
    Builds a steel retaining wall along an edge curve.

    Notes:
        - Wall columns are positioned along the edge curve at intervals defined by STEEL_STEP_LENGTH.
        - Columns follow a zigzag pattern defined by PHASE_SEQUENCE and STEEL_ZIGZAG_AMPLITUDE.
        - Wall height is determined relative to the underpass curve and CONCRETE_EDGE_HEIGHT.
    """
    edge_curve = bpy.data.objects[EDGE_CURVE]
    under_curve = bpy.data.objects[UNDERPASS_CURVE]
    edge_pts = sample_curve_eval(edge_curve)
    under_pts = sample_curve_eval(under_curve)
    edge_lengths, edge_total = cumulative_lengths(edge_pts)
    mesh = bpy.data.meshes.new("SteelRetainingWall")
    obj = bpy.data.objects.new("SteelRetainingWall", mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    columns = []
    cumulative_offset = 0.0
    if STEEL_ZIGZAG:
        step_length = STEEL_STEP_LENGTH
    else:
        step_length = STEEL_STEP_LENGTH * 8
    segment_count = math.ceil(edge_total / step_length)
    for i in range(segment_count + 1):
        dist = min(i * step_length, edge_total)
        edge_pt = sample_by_distance(edge_pts, edge_lengths, edge_total, dist)
        under_pt = closest_point_xy(edge_pt, under_pts)
        steel_bottom = under_pt.z - 0.5
        concrete_bottom_z = edge_pt.z - CONCRETE_EDGE_HEIGHT
        steel_top = max(concrete_bottom_z, steel_bottom)
        next_dist = min(dist + STEEL_STEP_LENGTH, edge_total)
        edge_pt_next = sample_by_distance(edge_pts, edge_lengths, edge_total, next_dist)
        direction = (edge_pt_next - edge_pt).to_2d().normalized()
        perp = -Vector((-direction.y, direction.x, 0))
        if STEEL_ZIGZAG:
            phase = PHASE_SEQUENCE[i % len(PHASE_SEQUENCE)]
            if phase == 0:
                cumulative_offset -= STEEL_ZIGZAG_AMPLITUDE
            elif phase == 1:
                cumulative_offset += STEEL_ZIGZAG_AMPLITUDE
        else:
            cumulative_offset = 0.0
        offset = perp * cumulative_offset
        v_bottom = bm.verts.new(Vector((edge_pt.x, edge_pt.y, steel_bottom)) + offset)
        v_top = bm.verts.new(Vector((edge_pt.x, edge_pt.y, steel_top)) + offset)
        columns.append((v_bottom, v_top))
    bm.verts.ensure_lookup_table()
    for i in range(len(columns)-1):
        c1 = columns[i]
        c2 = columns[i+1]
        if (c1[0].co.z == c1[1].co.z) and (c2[0].co.z == c2[1].co.z):
            continue
        if STEEL_FLIP_FACES:
            bm.faces.new([c1[1], c2[1], c2[0], c1[0]])
        else:
            bm.faces.new([c1[0], c2[0], c2[1], c1[1]])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()


def build_concrete_edge():
    """
    Builds a concrete edge retaining wall along an edge curve.

    Notes:
        - Wall geometry is created between the edge curve and underpass curve.
        - Wall thickness is defined by CONCRETE_EDGE_THICKNESS.
        - Concrete height is limited by CONCRETE_EDGE_HEIGHT and underpass elevation.
        - Generates front/back and top/bottom faces of the wall mesh.
    """
    edge_curve = bpy.data.objects[EDGE_CURVE]
    under_curve = bpy.data.objects[UNDERPASS_CURVE]
    edge_pts = sample_curve_eval(edge_curve)
    under_pts = sample_curve_eval(under_curve)
    mesh = bpy.data.meshes.new("SteelRetainingWallEdge")
    obj = bpy.data.objects.new("SteelRetainingWallEdge", mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    front_bottom = []
    front_top = []
    back_bottom = []
    back_top = []
    for i, edge_pt in enumerate(edge_pts):
        under_pt = closest_point_xy(edge_pt, under_pts)
        total_height = edge_pt.z - under_pt.z + 0.5
        if total_height <= 0:
            front_bottom.append(None)
            front_top.append(None)
            back_bottom.append(None)
            back_top.append(None)
            continue
        if i < len(edge_pts)-1:
            direction = (edge_pts[i+1] - edge_pts[i]).to_2d().normalized()
        else:
            direction = (edge_pts[i] - edge_pts[i-1]).to_2d().normalized()
        perp = Vector((-direction.y, direction.x, 0)) * (CONCRETE_EDGE_THICKNESS / 2)
        concrete_top_z = edge_pt.z
        concrete_bottom_z = max(edge_pt.z - CONCRETE_EDGE_HEIGHT, under_pt.z - 0.5)
        fb = bm.verts.new(Vector((edge_pt.x, edge_pt.y, concrete_bottom_z)) - perp)
        bb = bm.verts.new(Vector((edge_pt.x, edge_pt.y, concrete_bottom_z)) + perp)
        ft = bm.verts.new(Vector((edge_pt.x, edge_pt.y, concrete_top_z)) - perp)
        bt = bm.verts.new(Vector((edge_pt.x, edge_pt.y, concrete_top_z)) + perp)
        front_bottom.append(fb)
        front_top.append(ft)
        back_bottom.append(bb)
        back_top.append(bt)
    bm.verts.ensure_lookup_table()
    for i in range(len(edge_pts) - 1):
        if not front_bottom[i] or not front_bottom[i+1]:
            continue
        bm.faces.new([front_bottom[i], front_bottom[i+1], front_top[i+1], front_top[i]])
        bm.faces.new([back_bottom[i], back_top[i], back_top[i+1], back_bottom[i+1]])
        bm.faces.new([front_top[i], front_top[i+1], back_top[i+1], back_top[i]])
        bm.faces.new([front_bottom[i], back_bottom[i], back_bottom[i+1], front_bottom[i+1]])
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


build_steel_rwall()
build_concrete_edge()