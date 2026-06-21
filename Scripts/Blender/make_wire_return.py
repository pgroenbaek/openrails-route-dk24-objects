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
import math
from math import sin, cos, pi
from mathutils import Vector

CURVE_NAME = "Overpass1"

MATERIAL_NAME = "Wire"

RETURN_WIRE_RESOLUTION = 6
RETURN_WIRE_THICKNESS = 0.03
RETURN_WIRE_SAG_RATIO = 0.01

WORLD_UP = Vector((0, 0, 1))

PROFILE_RETURN_WIRE = [
    (Vector((0.0,  RETURN_WIRE_THICKNESS / 2.0)), Vector((0.0, 0.9727))),
    (Vector((RETURN_WIRE_THICKNESS / 2.0, 0.0)), Vector((0.0, 0.9492))),
    (Vector((0.0, -(RETURN_WIRE_THICKNESS / 2.0))), Vector((0.0, 0.9727))),
    (Vector((-(RETURN_WIRE_THICKNESS / 2.0), 0.0)), Vector((0.0, 0.9492))),
]

MAST_TYPES = {
    "A": {"return_offset": Vector((0.0, 7.0))},
    "B": {"return_offset": Vector((0.1, 6.9))},
    "C": {"return_offset": Vector((-0.1, 7.2))},
}

MASTS = [
    (0.05, "A"),
    (0.22, "B"),
    (0.41, "A"),
    (0.63, "C"),
    (0.91, "B"),
]


def sample_curve(curve_object):
    """
    Samples points from a Blender curve object after evaluation.

    Args:
        curve_object (bpy.types.Object): The Blender curve object to sample.

    Returns:
        List[Vector]: A list of 3D points (Vector) representing the sampled curve.
    """
    dependency_graph = bpy.context.evaluated_depsgraph_get()
    evaluated_curve_object = curve_object.evaluated_get(dependency_graph)
    evaluated_mesh = evaluated_curve_object.to_mesh()
    sampled_points = [vertex.co.copy() for vertex in evaluated_mesh.vertices]
    evaluated_curve_object.to_mesh_clear()
    return sampled_points


def eval_curve(curve_points, interpolation_factor):
    """
    Evaluates a point on a polyline curve using linear interpolation.

    Args:
        curve_points (List[Vector]): List of points defining the polyline.
        interpolation_factor (float): Factor between 0.0 and 1.0 for interpolation.

    Returns:
        Vector: The interpolated 3D point on the curve.
    """
    point_count = len(curve_points)
    floating_index = interpolation_factor * (point_count - 1)
    lower_index = int(floating_index)
    upper_index = min(lower_index + 1, point_count - 1)
    return curve_points[lower_index].lerp(curve_points[upper_index], floating_index - lower_index)


def build_return_wire(curve_points):
    """
    Generates the mesh for the return overhead wire.

    The wire path is determined by attachment points defined in the global MASTS list
    and interpolated along the main curve_points. Sag is applied based on a
    ratio of the span length for each segment.

    Args:
        curve_points (List[Vector]): Sampled points from the main curve path.

    Returns:
        bpy.types.Object: The created Blender object for the return wire, or None if no masts are defined.
    """
    return_wire_attachment_points = []
    for normalized_t, mast_type_key in MASTS:
        mast_position_on_curve = eval_curve(curve_points, normalized_t)
        if mast_type_key not in MAST_TYPES:
            print(f"Warning: Mast type '{mast_type_key}' not defined in MAST_TYPES. Skipping mast at t={normalized_t}.")
            continue
        mast_definition = MAST_TYPES[mast_type_key]
        return_offset = mast_definition.get("return_offset")
        if return_offset is None:
            print(f"Warning: 'return_offset' not found for mast type '{mast_type_key}'. Using curve position for mast at t={normalized_t}.")
            final_attachment_point = mast_position_on_curve
        else:
            final_attachment_point = mast_position_on_curve + Vector((return_offset.x, 0, return_offset.y))
        return_wire_attachment_points.append(final_attachment_point)
    return_wire_path_points = []
    for segment_index in range(len(return_wire_attachment_points) - 1):
        start_point = return_wire_attachment_points[segment_index]
        end_point = return_wire_attachment_points[segment_index + 1]
        span_length = (end_point - start_point).length
        max_sag_for_this_span = span_length * RETURN_WIRE_SAG_RATIO
        for span_sub_index in range(RETURN_WIRE_RESOLUTION + 1):
            interpolation_factor = span_sub_index / RETURN_WIRE_RESOLUTION
            interpolated_base_point = start_point.lerp(end_point, interpolation_factor)
            arch_factor = 4 * interpolation_factor * (1 - interpolation_factor)
            sag_amount = max_sag_for_this_span * arch_factor
            wire_point = interpolated_base_point - WORLD_UP * sag_amount
            return_wire_path_points.append(wire_point)
    if not return_wire_path_points:
        print("Warning: No path points generated for return wire. Skipping mesh creation.")
        return None
    mesh_vertices = []
    mesh_uvs = []
    mesh_faces = []
    profile_point_count = len(PROFILE_RETURN_WIRE)
    for i in range(len(return_wire_path_points)):
        current_path_point = return_wire_path_points[i]
        if i < len(return_wire_path_points) - 1:
            segment_direction = (return_wire_path_points[i+1] - current_path_point)
        elif i > 0:
            segment_direction = (current_path_point - return_wire_path_points[i-1])
        else:
            segment_direction = Vector((1, 0, 0))
        if segment_direction.length_squared < 1e-6:
            segment_direction = Vector((1, 0, 0))
        else:
            segment_direction.normalize()
        right_vector = segment_direction.cross(WORLD_UP)
        if right_vector.length_squared < 1e-6:
            if abs(segment_direction.dot(Vector((0,1,0)))) > 0.9:
                right_vector = segment_direction.cross(Vector((1,0,0))).normalized()
            else:
                right_vector = segment_direction.cross(Vector((0,1,0))).normalized()
        else:
            right_vector.normalize()
        upward_vector = right_vector.cross(segment_direction).normalized()
        base_vertex_index = len(mesh_vertices)
        for profile_offset, texcoord in PROFILE_RETURN_WIRE:
            mesh_vertices.append(
                current_path_point +
                right_vector * profile_offset.x +
                upward_vector * profile_offset.y
            )
            mesh_uvs.append(texcoord)
        if i > 0:
            previous_base_vertex_index = base_vertex_index - profile_point_count
            for p_idx in range(profile_point_count):
                next_p_idx = (p_idx + 1) % profile_point_count
                mesh_faces.append((
                    previous_base_vertex_index + p_idx,
                    previous_base_vertex_index + next_p_idx,
                    base_vertex_index + next_p_idx,
                    base_vertex_index + p_idx
                ))
    mesh = bpy.data.meshes.new("ReturnWire")
    obj = bpy.data.objects.new("ReturnWire", mesh)
    bpy.context.collection.objects.link(obj)
    material = bpy.data.materials.get(MATERIAL_NAME)
    if material is None:
        material = bpy.data.materials.new(MATERIAL_NAME)
    if material.name not in obj.data.materials:
        obj.data.materials.append(material)
    material_index = obj.data.materials.find(material.name)
    mesh.from_pydata(mesh_vertices, [], mesh_faces)
    mesh.update()
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(180))
    mesh.polygons.foreach_set("material_index", [material_index] * len(mesh.polygons))
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = mesh_uvs[vertex_index]
    return obj


def make_return_wire():
    """
    Main execution function that generates the return overhead wire system.
    """
    curve_object = bpy.data.objects.get(CURVE_NAME)
    curve_points = sample_curve(curve_object)
    build_return_wire(curve_points)



make_return_wire()
