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
import math
from mathutils import Vector


EDGE_CURVE = "RailingCurve5"
UNDERPASS_CURVE = "Underpass"

RWALL_EDGE_THICKNESS = 0.5 # 0.5
RWALL_EDGE_HEIGHT = 0.1 # 0.3 for Concrete, 0.1 for RustySteel
RWALL_EDGE_OFFSET = 0.05
RWALL_EDGE_MATERIAL_NAME = "RustySteel" # Concrete, RustySteel
RWALL_EDGE_U_PER_METER = 0.1
RWALL_EDGE_V_PER_METER = 0.1

RWALL_ZIGZAG = True
RWALL_FLIP_FACES = True
RWALL_MATERIAL_NAME = "RustySteel" # RustySteel
RWALL_U_PER_METER = 0.1
RWALL_V_PER_METER = 0.1

ZIGZAG_AMPLITUDE = 0.2
ZIGZAG_STEP_LENGTH = 0.6
ZIGZAG_PHASE_SEQUENCE = [2, 0, 2, 1] # 0=left, 1=right, 2=straight


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
        lengths.append(lengths[-1] + (points[i] - points[i - 1]).length)
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
    for i in range(len(lengths) - 1):
        if lengths[i] <= dist <= lengths[i + 1]:
            segment_ratio = (dist - lengths[i]) / (lengths[i + 1] - lengths[i])
            return points[i].lerp(points[i + 1], segment_ratio)
    return points[-1]


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


def split_crossing_z(v_bottom_z, v_top_z, next_bottom_z, next_top_z):
    """
    Computes Z-axis crossover points for a wall segment and returns interpolation fractions.

    Args:
        v_bottom_z (float): Z-coordinate of the bottom vertex of the current segment.
        v_top_z (float): Z-coordinate of the top vertex of the current segment.
        next_bottom_z (float): Z-coordinate of the bottom vertex of the next segment.
        next_top_z (float): Z-coordinate of the top vertex of the next segment.

    Returns:
        List[float]: Sorted list of interpolation fractions (between 0.0 and 1.0) 
        indicating where along the segment a split is needed. Empty list if no crossover.
    """
    fractions = []
    if (v_bottom_z - next_bottom_z) * (v_top_z - next_top_z) < 0:
        t = (v_bottom_z - next_bottom_z) / ((v_bottom_z - next_bottom_z) - (v_top_z - next_top_z))
        fractions.append(max(0.0, min(1.0, t)))
    return sorted(fractions)

def build_steel_rwall():
    """
    Builds a steel retaining wall along an edge curve.

    Notes:
        - Wall columns are positioned along the edge curve at intervals defined by ZIGZAG_STEP_LENGTH.
        - Columns follow a zigzag pattern defined by ZIGZAG_PHASE_SEQUENCE and ZIGZAG_AMPLITUDE.
        - Wall height is determined relative to the underpass curve and RWALL_EDGE_HEIGHT.
        - Handles crossover between steel bottom and concrete bottom.
    """
    edge_curve = bpy.data.objects[EDGE_CURVE]
    under_curve = bpy.data.objects[UNDERPASS_CURVE]
    edge_points = sample_curve_eval(edge_curve)
    under_points = sample_curve_eval(under_curve)
    edge_lengths, edge_total = cumulative_lengths(edge_points)
    mesh = bpy.data.meshes.new("SteelRetainingWall")
    obj = bpy.data.objects.new("SteelRetainingWall", mesh)
    bpy.context.collection.objects.link(obj)
    material = bpy.data.materials.get(RWALL_MATERIAL_NAME)
    if material is None:
        material = bpy.data.materials.new(RWALL_MATERIAL_NAME)
    if material.name not in obj.data.materials:
        obj.data.materials.append(material)
    material_index = obj.data.materials.find(material.name)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    cumulative_offset = 0.0
    step_length = ZIGZAG_STEP_LENGTH if RWALL_ZIGZAG else ZIGZAG_STEP_LENGTH * 8
    segment_count = math.ceil(edge_total / step_length)
    columns = []
    for i in range(segment_count + 1):
        dist = min(i * step_length, edge_total)
        edge_point = sample_by_distance(edge_points, edge_lengths, edge_total, dist)
        under_point = closest_point_xy(edge_point, under_points)
        steel_bottom = under_point.z - 0.5
        concrete_bottom_z = edge_point.z - RWALL_EDGE_HEIGHT
        steel_top = max(concrete_bottom_z, steel_bottom)
        next_dist = min(dist + ZIGZAG_STEP_LENGTH, edge_total)
        edge_point_next = sample_by_distance(edge_points, edge_lengths, edge_total, next_dist)
        direction = (edge_point_next - edge_point).to_2d().normalized()
        if RWALL_ZIGZAG:
            phase = ZIGZAG_PHASE_SEQUENCE[i % len(ZIGZAG_PHASE_SEQUENCE)]
            if phase == 0:
                cumulative_offset -= ZIGZAG_AMPLITUDE
            elif phase == 1:
                cumulative_offset += ZIGZAG_AMPLITUDE
        perp = -Vector((-direction.y, direction.x, 0))
        steel_offset = perp * cumulative_offset
        v_bottom = bm.verts.new(Vector((edge_point.x, edge_point.y, steel_bottom)) + steel_offset)
        v_top = bm.verts.new(Vector((edge_point.x, edge_point.y, steel_top)) + steel_offset)
        columns.append((v_bottom, v_top))
    bm.verts.ensure_lookup_table()
    running_length = 0.0
    for i in range(len(columns) - 1):
        c1_bottom, c1_top = columns[i]
        c2_bottom, c2_top = columns[i + 1]
        fractions = split_crossing_z(c1_bottom.co.z, c1_top.co.z, c2_bottom.co.z, c2_top.co.z)
        split_points = [0.0] + fractions + [1.0]
        for j in range(len(split_points) - 1):
            t0 = split_points[j]
            t1 = split_points[j + 1]
            b_start = c1_bottom.co.lerp(c2_bottom.co, t0)
            t_start = c1_top.co.lerp(c2_top.co, t0)
            b_end = c1_bottom.co.lerp(c2_bottom.co, t1)
            t_end = c1_top.co.lerp(c2_top.co, t1)
            segment_length = (b_end - b_start).length
            u1 = running_length * RWALL_U_PER_METER
            u2 = (running_length + segment_length) * RWALL_U_PER_METER
            running_length += segment_length
            height1 = t_start.z - b_start.z
            height2 = t_end.z - b_end.z
            v1 = height1 * RWALL_V_PER_METER
            v2 = height2 * RWALL_V_PER_METER
            if RWALL_FLIP_FACES:
                face = bm.faces.new([
                    bm.verts.new(t_start),
                    bm.verts.new(t_end),
                    bm.verts.new(b_end),
                    bm.verts.new(b_start)])
                loops = face.loops
                loops[0][uv_layer].uv = (u1, v1)
                loops[1][uv_layer].uv = (u2, v2)
                loops[2][uv_layer].uv = (u2, 0)
                loops[3][uv_layer].uv = (u1, 0)
            else:
                face = bm.faces.new([
                    bm.verts.new(b_start),
                    bm.verts.new(b_end),
                    bm.verts.new(t_end),
                    bm.verts.new(t_start)])
                loops = face.loops
                loops[0][uv_layer].uv = (u1, 0)
                loops[1][uv_layer].uv = (u2, 0)
                loops[2][uv_layer].uv = (u2, v2)
                loops[3][uv_layer].uv = (u1, v1)
            face.material_index = material_index
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()


def build_steel_rwall_edge():
    """
    Builds an upper edge for the retaining wall along an edge curve.

    Notes:
        - Wall geometry is created between the edge curve and underpass curve.
        - Wall thickness is defined by RWALL_EDGE_THICKNESS.
        - Concrete height is limited by RWALL_EDGE_HEIGHT and underpass elevation.
        - Handles crossover along Z-axis and creates faces for each section.
    """
    edge_curve = bpy.data.objects[EDGE_CURVE]
    under_curve = bpy.data.objects[UNDERPASS_CURVE]
    edge_points = sample_curve_eval(edge_curve)
    under_points = sample_curve_eval(under_curve)
    mesh = bpy.data.meshes.new("SteelRetainingWallEdge")
    obj = bpy.data.objects.new("SteelRetainingWallEdge", mesh)
    bpy.context.collection.objects.link(obj)
    material = bpy.data.materials.get(RWALL_EDGE_MATERIAL_NAME)
    if material is None:
        material = bpy.data.materials.new(RWALL_EDGE_MATERIAL_NAME)
    if material.name not in obj.data.materials:
        obj.data.materials.append(material)
    material_index = obj.data.materials.find(material.name)
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    columns = []
    for i, edge_point in enumerate(edge_points):
        under_point = closest_point_xy(edge_point, under_points)
        concrete_top_z = edge_point.z
        concrete_bottom_z = max(edge_point.z - RWALL_EDGE_HEIGHT, under_point.z - RWALL_EDGE_HEIGHT - 0.5)
        if concrete_top_z - concrete_bottom_z <= 0:
            columns.append((None, None, None, None))
            continue
        direction = (edge_points[i + 1] - edge_points[i]).to_2d().normalized() if i < len(edge_points) - 1 else (edge_points[i] - edge_points[i - 1]).to_2d().normalized()
        perp = Vector((-direction.y, direction.x, 0))
        thickness_offset = perp * (RWALL_EDGE_THICKNESS / 2)
        edge_offset = perp * RWALL_EDGE_OFFSET
        edge_pos = Vector((edge_point.x, edge_point.y, 0)) + edge_offset
        fb = bm.verts.new(Vector((edge_pos.x, edge_pos.y, concrete_bottom_z)) - thickness_offset)
        bb = bm.verts.new(Vector((edge_pos.x, edge_pos.y, concrete_bottom_z)) + thickness_offset)
        ft = bm.verts.new(Vector((edge_pos.x, edge_pos.y, concrete_top_z)) - thickness_offset)
        bt = bm.verts.new(Vector((edge_pos.x, edge_pos.y, concrete_top_z)) + thickness_offset)
        columns.append((fb, ft, bb, bt))
    bm.verts.ensure_lookup_table()
    running_length = 0.0
    for i in range(len(columns) - 1):
        c1_fb, c1_ft, c1_bb, c1_bt = columns[i]
        c2_fb, c2_ft, c2_bb, c2_bt = columns[i + 1]
        if c1_fb is None or c2_fb is None:
            continue
        fractions = split_crossing_z(c1_fb.co.z, c1_ft.co.z, c2_fb.co.z, c2_ft.co.z)
        split_points = [0.0] + fractions + [1.0]
        for j in range(len(split_points) - 1):
            t0 = split_points[j]
            t1 = split_points[j + 1]
            fb_start = bm.verts.new(c1_fb.co.lerp(c2_fb.co, t0))
            ft_start = bm.verts.new(c1_ft.co.lerp(c2_ft.co, t0))
            bb_start = bm.verts.new(c1_bb.co.lerp(c2_bb.co, t0))
            bt_start = bm.verts.new(c1_bt.co.lerp(c2_bt.co, t0))
            fb_end = bm.verts.new(c1_fb.co.lerp(c2_fb.co, t1))
            ft_end = bm.verts.new(c1_ft.co.lerp(c2_ft.co, t1))
            bb_end = bm.verts.new(c1_bb.co.lerp(c2_bb.co, t1))
            bt_end = bm.verts.new(c1_bt.co.lerp(c2_bt.co, t1))
            #if fb_start.co.z > ft_start.co.z:
            #    fb_start, ft_start = ft_start, fb_start
            #if bb_start.co.z > bt_start.co.z:
            #    bb_start, bt_start = bt_start, bb_start
            #if fb_end.co.z > ft_end.co.z:
            #    fb_end, ft_end = ft_end, fb_end
            #if bb_end.co.z > bt_end.co.z:
            #    bb_end, bt_end = bt_end, bb_end
            segment_length = (fb_end.co - fb_start.co).length
            u1 = running_length * RWALL_EDGE_U_PER_METER
            u2 = (running_length + segment_length) * RWALL_EDGE_U_PER_METER
            running_length += segment_length
            height_start = ft_start.co.z - fb_start.co.z
            height_end = ft_end.co.z - fb_end.co.z
            v1 = height_start * RWALL_EDGE_V_PER_METER
            v2 = height_end * RWALL_EDGE_V_PER_METER
            v_top = RWALL_EDGE_THICKNESS * RWALL_EDGE_V_PER_METER
            face = bm.faces.new([fb_start, fb_end, ft_end, ft_start])
            face.material_index = material_index
            loops = face.loops
            loops[0][uv_layer].uv = (u1, 0)
            loops[1][uv_layer].uv = (u2, 0)
            loops[2][uv_layer].uv = (u2, v2)
            loops[3][uv_layer].uv = (u1, v1)
            face = bm.faces.new([bb_start, bt_start, bt_end, bb_end])
            face.material_index = material_index
            loops = face.loops
            loops[0][uv_layer].uv = (u1, 0)
            loops[1][uv_layer].uv = (u1, v1)
            loops[2][uv_layer].uv = (u2, v2)
            loops[3][uv_layer].uv = (u2, 0)
            face = bm.faces.new([ft_start, ft_end, bt_end, bt_start])
            face.material_index = material_index
            loops = face.loops
            loops[0][uv_layer].uv = (u1, 0)
            loops[1][uv_layer].uv = (u2, 0)
            loops[2][uv_layer].uv = (u2, v_top)
            loops[3][uv_layer].uv = (u1, v_top)
            face = bm.faces.new([fb_start, bb_start, bb_end, fb_end])
            face.material_index = material_index
            loops = face.loops
            loops[0][uv_layer].uv = (u1, 0)
            loops[1][uv_layer].uv = (u1, v_top)
            loops[2][uv_layer].uv = (u2, v_top)
            loops[3][uv_layer].uv = (u2, 0)
    for c_fb, c_ft, c_bb, c_bt in columns:
        if c_fb:
            start_face = bm.faces.new([c_fb, c_bb, c_bt, c_ft])
            start_face.material_index = material_index
            height = c_ft.co.z - c_fb.co.z
            v = height * RWALL_EDGE_V_PER_METER
            u = RWALL_EDGE_THICKNESS * RWALL_EDGE_U_PER_METER
            loops = start_face.loops
            loops[0][uv_layer].uv = (0, 0)
            loops[1][uv_layer].uv = (u, 0)
            loops[2][uv_layer].uv = (u, v)
            loops[3][uv_layer].uv = (0, v)
            break
    for c_fb, c_ft, c_bb, c_bt in reversed(columns):
        if c_fb:
            end_face = bm.faces.new([c_fb, c_ft, c_bt, c_bb])
            end_face.material_index = material_index
            height = c_ft.co.z - c_fb.co.z
            v = height * RWALL_EDGE_V_PER_METER
            u = RWALL_EDGE_THICKNESS * RWALL_EDGE_U_PER_METER
            loops = end_face.loops
            loops[0][uv_layer].uv = (0, 0)
            loops[1][uv_layer].uv = (0, v)
            loops[2][uv_layer].uv = (u, v)
            loops[3][uv_layer].uv = (u, 0)
            break
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()


build_steel_rwall()
build_steel_rwall_edge()
