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
from math import sin, cos, pi
from mathutils import Vector

# TODO UV mapping
# TODO Configure offsets in MAST_TYPES dict
# TODO Load mast positions from world files based on UiD's and tile X/Y
# TODO Project mast positions onto the curve to populate the MASTS list

CURVE_NAME = "Overpass1"

SPAN_RESOLUTION = 24
CONNECTOR_STEP = 4

ARCH_CLEARANCE = 0.4
ARCH_HEIGHT = 0.2

CONNECTOR_RADIUS = 0.005
CONNECTOR_COLLAR_RADIUS = CONNECTOR_RADIUS * 1.25
CONNECTOR_COLLAR_LENGTH = 0.03
CONNECTOR_NUM_SIDES = 3

WORLD_UP = Vector((0, 0, 1))

PROFILE_TOP = [
    (Vector((0.0000, -0.0100)), Vector((0, 1, 0))),
    (Vector((0.0060, 0.0000)), Vector((0,-1, 0))),
    (Vector((-0.0060, 0.0000)), Vector((0,-1, 0))),
]
PROFILE_BOTTOM = [
    (Vector((0.0000, 0.0101)), Vector((0, 1, 0))),
    (Vector((0.0060, 0.0000)), Vector((0,-1, 0))),
    (Vector((-0.0060, 0.0000)), Vector((0,-1, 0))),
]

MAST_TYPES = {
    "A": {"top": Vector((0.25, 7.1999)), "bottom": Vector((-0.25, 6.1999))},
    "B": {"top": Vector((-0.35, 7.1999)), "bottom": Vector((0.20, 6.1999))},
    "C": {"top": Vector((0.15, 7.1999)), "bottom": Vector((-0.30, 6.1999))},
}

MASTS = [
    (0.05, "A"),
    (0.22, "B"),
    (0.41, "A"),
    (0.63, "C"),
    (0.91, "B"),
]


def sample_curve(curve_object):
    dependency_graph = bpy.context.evaluated_depsgraph_get()
    evaluated_curve_object = curve_object.evaluated_get(dependency_graph)
    evaluated_mesh = evaluated_curve_object.to_mesh()
    sampled_points = [vertex.co.copy() for vertex in evaluated_mesh.vertices]
    evaluated_curve_object.to_mesh_clear()
    return sampled_points


def eval_curve(curve_points, interpolation_factor):
    point_count = len(curve_points)
    floating_index = interpolation_factor * (point_count - 1)
    lower_index = int(floating_index)
    upper_index = min(lower_index + 1, point_count - 1)
    return curve_points[lower_index].lerp(curve_points[upper_index], floating_index - lower_index)


def build_masts(curve_points):
    top_mast_points = []
    bottom_mast_points = []
    for normalized_t, mast_type_key in MASTS:
        mast_position = eval_curve(curve_points, normalized_t)
        mast_definition = MAST_TYPES[mast_type_key]
        top_mast_points.append(mast_position + Vector((mast_definition["top"].x, 0, mast_definition["top"].y)))
        bottom_mast_points.append(mast_position + Vector((mast_definition["bottom"].x, 0, mast_definition["bottom"].y)))
    return top_mast_points, bottom_mast_points


def build_top_wire(top_mast_points, bottom_mast_points):
    top_wire_points = []
    mesh_vertices = []
    mesh_faces = []
    profile_point_count = len(PROFILE_TOP)
    for segment_index in range(len(top_mast_points) - 1):
        start_top_point, end_top_point = top_mast_points[segment_index], top_mast_points[segment_index + 1]
        start_bottom_point, end_bottom_point = bottom_mast_points[segment_index], bottom_mast_points[segment_index + 1]
        for span_index in range(SPAN_RESOLUTION + 1):
            interpolation_factor = span_index / SPAN_RESOLUTION
            interpolated_top_x = start_top_point.x * (1 - interpolation_factor) + end_top_point.x * interpolation_factor
            interpolated_top_y = start_top_point.y * (1 - interpolation_factor) + end_top_point.y * interpolation_factor
            interpolated_top_base_z = start_top_point.z * (1 - interpolation_factor) + end_top_point.z * interpolation_factor
            arch_factor = 4 * interpolation_factor * (1 - interpolation_factor)
            sag_amount = ARCH_HEIGHT * arch_factor
            interpolated_top_z = interpolated_top_base_z - sag_amount
            interpolated_bottom_point = Vector((
                start_bottom_point.x * (1 - interpolation_factor) + end_bottom_point.x * interpolation_factor,
                start_bottom_point.y * (1 - interpolation_factor) + end_bottom_point.y * interpolation_factor,
                start_bottom_point.z * (1 - interpolation_factor) + end_bottom_point.z * interpolation_factor,
            ))
            minimum_allowed_z = interpolated_bottom_point.z + ARCH_CLEARANCE
            if interpolated_top_z < minimum_allowed_z:
                interpolated_top_z += (minimum_allowed_z - interpolated_top_z) * 0.35
            wire_point = Vector((interpolated_top_x, interpolated_top_y, interpolated_top_z))
            top_wire_points.append(wire_point)
            if len(top_wire_points) == 1:
                segment_direction = end_top_point - start_top_point
            else:
                segment_direction = wire_point - top_wire_points[-2]
            if segment_direction.length == 0:
                segment_direction = Vector((1, 0, 0))
            else:
                segment_direction.normalize()
            upward_vector = wire_point - interpolated_bottom_point
            if upward_vector.length == 0:
                upward_vector = WORLD_UP
            else:
                upward_vector.normalize()
            right_vector = segment_direction.cross(upward_vector)
            if right_vector.length == 0:
                right_vector = Vector((1, 0, 0))
            else:
                right_vector.normalize()
            upward_vector = right_vector.cross(segment_direction).normalized()
            base_vertex_index = len(mesh_vertices)
            for profile_offset, _ in PROFILE_TOP:
                mesh_vertices.append(
                    wire_point +
                    right_vector * profile_offset.x +
                    upward_vector * profile_offset.y
                )
            if base_vertex_index >= profile_point_count:
                previous_base_vertex_index = base_vertex_index - profile_point_count
                mesh_faces.append((
                    previous_base_vertex_index + 0,
                    previous_base_vertex_index + 1,
                    base_vertex_index + 1,
                    base_vertex_index + 0
                ))
                mesh_faces.append((
                    previous_base_vertex_index + 1,
                    previous_base_vertex_index + 2,
                    base_vertex_index + 2,
                    base_vertex_index + 1
                ))
                mesh_faces.append((
                    previous_base_vertex_index + 2,
                    previous_base_vertex_index + 0,
                    base_vertex_index + 0,
                    base_vertex_index + 2
                ))
    mesh = bpy.data.meshes.new("TopWire")
    obj = bpy.data.objects.new("TopWire", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.from_pydata(mesh_vertices, [], mesh_faces)
    mesh.update()
    return top_wire_points


def build_bottom_wire(top_mast_points, bottom_mast_points):
    bottom_wire_points = []
    mesh_vertices = []
    mesh_faces = []
    profile_point_count = len(PROFILE_BOTTOM)
    for mast_index, mast_position in enumerate(bottom_mast_points):
        bottom_wire_points.append(mast_position)
        if len(bottom_mast_points) == 1:
            segment_direction = Vector((1, 0, 0))
        elif mast_index < len(bottom_mast_points) - 1:
            segment_direction = bottom_mast_points[mast_index + 1] - mast_position
        else:
            segment_direction = mast_position - bottom_mast_points[mast_index - 1]
        if segment_direction.length == 0:
            segment_direction = Vector((1, 0, 0))
        else:
            segment_direction.normalize()
        upward_vector = top_mast_points[mast_index] - mast_position
        if upward_vector.length == 0:
            upward_vector = WORLD_UP
        else:
            upward_vector.normalize()
        right_vector = segment_direction.cross(upward_vector)
        if right_vector.length == 0:
            right_vector = Vector((1, 0, 0))
        else:
            right_vector.normalize()
        upward_vector = right_vector.cross(segment_direction).normalized()
        base_vertex_index = len(mesh_vertices)
        for profile_offset, _ in PROFILE_BOTTOM:
            mesh_vertices.append(
                mast_position +
                right_vector * profile_offset.x +
                upward_vector * profile_offset.y
            )
        if base_vertex_index >= profile_point_count:
            previous_base_vertex_index = base_vertex_index - profile_point_count
            mesh_faces.append((
                previous_base_vertex_index + 0,
                previous_base_vertex_index + 1,
                base_vertex_index + 1,
                base_vertex_index + 0
            ))
            mesh_faces.append((
                previous_base_vertex_index + 1,
                previous_base_vertex_index + 2,
                base_vertex_index + 2,
                base_vertex_index + 1
            ))
            mesh_faces.append((
                previous_base_vertex_index + 2,
                previous_base_vertex_index + 0,
                base_vertex_index + 0,
                base_vertex_index + 2
            ))
    mesh = bpy.data.meshes.new("BottomWire")
    obj = bpy.data.objects.new("BottomWire", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.from_pydata(mesh_vertices, [], mesh_faces)
    mesh.update()
    return bottom_wire_points


def build_connectors(top_wire_points, bottom_wire_points):
    mesh_vertices = []
    mesh_faces = []
    for mast_index in range(0, len(top_wire_points), CONNECTOR_STEP):
        top_point = top_wire_points[mast_index]
        best_projection_point = None
        best_projection_distance = 1e18
        for segment_index in range(len(bottom_wire_points) - 1):
            segment_start_point = bottom_wire_points[segment_index]
            segment_end_point = bottom_wire_points[segment_index + 1]
            segment_direction = segment_end_point - segment_start_point
            segment_length_squared = segment_direction.length_squared
            if segment_length_squared == 0:
                continue
            projection_factor = (top_point - segment_start_point).dot(segment_direction) / segment_length_squared
            projection_factor = max(0.0, min(1.0, projection_factor))
            projected_point = segment_start_point + segment_direction * projection_factor
            projection_distance = (projected_point - top_point).length_squared
            if projection_distance < best_projection_distance:
                best_projection_distance = projection_distance
                best_projection_point = projected_point
        if best_projection_point is None:
            continue
        connector_axis = best_projection_point - top_point
        connector_length = connector_axis.length
        if connector_length <= CONNECTOR_COLLAR_LENGTH * 2.0:
            continue
        connector_direction = connector_axis.normalized()
        if abs(connector_direction.dot(WORLD_UP)) > 0.999:
            connector_right_vector = Vector((1, 0, 0))
        else:
            connector_right_vector = connector_direction.cross(WORLD_UP).normalized()
        connector_up_vector = connector_right_vector.cross(connector_direction).normalized()
        shaft_start_point = top_point + connector_direction * CONNECTOR_COLLAR_LENGTH
        shaft_end_point = best_projection_point - connector_direction * CONNECTOR_COLLAR_LENGTH
        base_vertex_index = len(mesh_vertices)
        for center_point in (shaft_start_point, shaft_end_point):
            for side_index in range(CONNECTOR_NUM_SIDES):
                angle = 2.0 * pi * side_index / CONNECTOR_NUM_SIDES
                mesh_vertices.append(
                    center_point + 
                    connector_right_vector * cos(angle) * CONNECTOR_RADIUS +
                    connector_up_vector * sin(angle) * CONNECTOR_RADIUS
                )
        for side_index in range(CONNECTOR_NUM_SIDES):
            next_side_index = (side_index + 1) % CONNECTOR_NUM_SIDES
            mesh_faces.append((
                base_vertex_index + side_index,
                base_vertex_index + next_side_index,
                base_vertex_index + CONNECTOR_NUM_SIDES + next_side_index,
                base_vertex_index + CONNECTOR_NUM_SIDES + side_index
            ))
        collar_start_point = top_point
        collar_end_point = top_point + connector_direction * CONNECTOR_COLLAR_LENGTH
        base_vertex_index = len(mesh_vertices)
        for center_point in (collar_start_point, collar_end_point):
            for side_index in range(CONNECTOR_NUM_SIDES):
                angle = 2.0 * pi * side_index / CONNECTOR_NUM_SIDES
                mesh_vertices.append(
                    center_point + 
                    connector_right_vector * cos(angle) * CONNECTOR_COLLAR_RADIUS + 
                    connector_up_vector * sin(angle) * CONNECTOR_COLLAR_RADIUS
                )
        for side_index in range(CONNECTOR_NUM_SIDES):
            next_side_index = (side_index + 1) % CONNECTOR_NUM_SIDES
            mesh_faces.append((
                base_vertex_index + side_index,
                base_vertex_index + next_side_index,
                base_vertex_index + CONNECTOR_NUM_SIDES + next_side_index,
                base_vertex_index + CONNECTOR_NUM_SIDES + side_index
            ))
        collar_start_point = best_projection_point - connector_direction * CONNECTOR_COLLAR_LENGTH
        collar_end_point = best_projection_point
        base_vertex_index = len(mesh_vertices)
        for center_point in (collar_start_point, collar_end_point):
            for side_index in range(CONNECTOR_NUM_SIDES):
                angle = 2.0 * pi * side_index / CONNECTOR_NUM_SIDES
                mesh_vertices.append(
                    center_point + 
                    connector_right_vector * cos(angle) * CONNECTOR_COLLAR_RADIUS + 
                    connector_up_vector * sin(angle) * CONNECTOR_COLLAR_RADIUS
                )
        for side_index in range(CONNECTOR_NUM_SIDES):
            next_side_index = (side_index + 1) % CONNECTOR_NUM_SIDES
            mesh_faces.append((
                base_vertex_index + side_index,
                base_vertex_index + next_side_index,
                base_vertex_index + CONNECTOR_NUM_SIDES + next_side_index,
                base_vertex_index + CONNECTOR_NUM_SIDES + side_index
            ))
    mesh = bpy.data.meshes.new("Connectors")
    obj = bpy.data.objects.new("Connectors", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.from_pydata(mesh_vertices, [], mesh_faces)
    mesh.update()


def make_wire():
    curve_object = bpy.data.objects[CURVE_NAME]
    curve_points = sample_curve(curve_object)
    top_mast_points, bottom_mast_points = build_masts(curve_points)
    top_wire_points = build_top_wire(top_mast_points, bottom_mast_points)
    bottom_wire_points = build_bottom_wire(top_mast_points, bottom_mast_points)
    build_connectors(top_wire_points, bottom_wire_points)


make_wire()



