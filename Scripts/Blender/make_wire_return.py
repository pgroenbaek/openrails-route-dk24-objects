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

MATERIAL_NAME = "Wire"

RETURN_WIRE_RESOLUTION = 6
RETURN_WIRE_THICKNESS = 0.03
RETURN_WIRE_SAG_RATIO = 0.01

WORLD_UP = Vector((0, 0, 1))
WORLD_FOLDER = "/media/peter/T7 Shield/Repos/personal/openrails-route-dk24/ROUTES/OR_DK24/WORLD"

TILE_SIZE = 2048

REFERENCE_POSITION_X = -874.908
REFERENCE_POSITION_Y = 14.4113
REFERENCE_POSITION_Z = -828.282
REFERENCE_TILE_X = -5656
REFERENCE_TILE_Y = 15119

PROFILE_RETURN_WIRE = [
    (Vector((0.0,  RETURN_WIRE_THICKNESS / 2.0)), Vector((0.0, 0.9727))),
    (Vector((RETURN_WIRE_THICKNESS / 2.0, 0.0)), Vector((0.0, 0.9492))),
    (Vector((0.0, -(RETURN_WIRE_THICKNESS / 2.0))), Vector((0.0, 0.9727))),
    (Vector((-(RETURN_WIRE_THICKNESS / 2.0), 0.0)), Vector((0.0, 0.9492))),
]

MAST_TYPES = {
    "PGA_DKGantry_N1t6m_KL.s": [
        {"return_offset": Vector((-2.799, 6.98))},
    ],
    "PGA_DKGantry_N1t6m_KR.s": [
        {"return_offset": Vector((-2.799, 6.98))},
    ],
    "PGA_DKGantry_N1t6m_LL.s": [
        {"return_offset": Vector((2.799, 6.98))},
    ],
    "PGA_DKGantry_N1t6m_LR.s": [
        {"return_offset": Vector((2.799, 6.98))},
    ],
    "PGA_DKGantry_N2t6m_K.s": [
        {"return_offset": Vector((5.299, 6.98))},
        {"return_offset": Vector((-5.299, 6.98))},
    ],
    "PGA_DKGantry_N2t6m_L.s": [
        {"return_offset": Vector((5.299, 6.98))},
        {"return_offset": Vector((-5.299, 6.98))},
    ],
}


MASTS = [
    #UiD, TileX, TileY, offset_index (for the specific shape within MAST_TYPES)
    # [6955, -5656, 15119, 0],
    # [6956, -5656, 15119, 0],
    # [6958, -5656, 15119, 0],
    # [6959, -5656, 15119, 0],
    # [6960, -5656, 15119, 0],
    # [6961, -5656, 15119, 0],
    # [112, -5657, 15119, 0],
    # [113, -5657, 15119, 0],
    # [3231, -5657, 15118, 0],
    # [3232, -5657, 15118, 0],
    # [3241, -5657, 15118, 0],
    # [3245, -5657, 15118, 0],
    # [3243, -5657, 15118, 0],
    # [3233, -5657, 15118, 0],
    # [3234, -5657, 15118, 0],
    # [3253, -5657, 15118, 0],
    # [3254, -5657, 15118, 0],
    ####
    [6955, -5656, 15119, 1],
    [6956, -5656, 15119, 1],
    [6958, -5656, 15119, 1],
    [6959, -5656, 15119, 1],
    [6960, -5656, 15119, 1],
    [6961, -5656, 15119, 1],
    [112, -5657, 15119, 1],
    [113, -5657, 15119, 1],
    [3231, -5657, 15118, 1],
    [3232, -5657, 15118, 1],
    [3240, -5657, 15118, 0],
    [3246, -5657, 15118, 0],
    [3248, -5657, 15118, 0],
    [3247, -5657, 15118, 0],
    [3233, -5657, 15118, 1],
    [3234, -5657, 15118, 1],
    [3253, -5657, 15118, 1],
    [3254, -5657, 15118, 1],
]


def calculate_blender_coordinates(position, tile_coords):
    """
    Calculates Blender coordinates based on position, tile coordinates, and a reference point.

    Args:
        position (Vector): The current position in game world coordinates (x, y, z).
        tile_coords (Vector): The tile coordinates (tile_x, tile_y) for the current position.

    Returns:
        Vector: The corresponding 3D point in Blender's coordinate system.
    """
    blender_x = (tile_coords.x - REFERENCE_TILE_X) * TILE_SIZE + (position.x - REFERENCE_POSITION_X)
    blender_y = (tile_coords.y - REFERENCE_TILE_Y) * TILE_SIZE + (position.z - REFERENCE_POSITION_Z)
    blender_z = position.y - REFERENCE_POSITION_Y
    return Vector((blender_x, blender_y, blender_z))


def read_mast_data():
    """
    Builds a list of mast data by reading required world tiles.

    Returns:
        List: [
            uid,
            tilex,
            tiley,
            filename,
            Vector(position),
            Quaternion(qdirection),
        ]
    """
    mast_data = []
    tiles_to_uids = {}
    track_nr_lookup = {}
    A = Matrix((
        (1, 0, 0, 0),
        (0, 0, 1, 0),
        (0, 1, 0, 0),
        (0, 0, 0, 1),
    ))
    for mast_entry in MASTS:
        uid = mast_entry[0]
        tile_x = mast_entry[1]
        tile_y = mast_entry[2]
        track_nr = mast_entry[3]
        key = (tile_x, tile_y, uid)
        if key not in track_nr_lookup:
            track_nr_lookup[key] = track_nr
        key = (tile_x, tile_y)
        if key not in tiles_to_uids:
            tiles_to_uids[key] = set()
        tiles_to_uids[key].add(uid)
    tile_cache = {}
    tile_data = {}
    for tile_coords in tiles_to_uids:
        tile_x = tile_coords[0]
        tile_y = tile_coords[1]
        filename = "w{:+07d}{:+07d}.w".format(tile_x, tile_y)
        file_path = Path(WORLD_FOLDER) / filename
        if not file_path.exists():
            print(f"Warning: Missing world file {filename}")
            continue
        uid = None
        file_name = None
        position = None
        qx = qy = qz = qw = None
        in_static = False
        lines = file_path.read_text(encoding="utf-16-le", errors="ignore").splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith("Static"):
                uid = None
                file_name = None
                position = None
                qx = qy = qz = qw = None
                in_static = True
                continue
            if in_static:
                if line.startswith("UiD"):
                    uid = int(line.split("(")[1].split(")")[0])
                elif line.startswith("FileName"):
                    file_name = line.split("(")[1].split(")")[0].strip()
                elif line.startswith("Position"):
                    parts = line.replace("Position", "").replace("(", "").replace(")", "").split()
                    if len(parts) >= 3:
                        position = Vector((float(parts[0]), float(parts[1]), float(parts[2])))
                elif line.startswith("QDirection"):
                    parts = line.replace("QDirection", "").replace("(", "").replace(")", "").split()
                    if len(parts) >= 4:
                        qx = float(parts[0])
                        qy = float(parts[1])
                        qz = float(parts[2])
                        qw = float(parts[3])
                elif ")" in line:
                    in_static = False
                    if uid in tiles_to_uids[(tile_x, tile_y)] and uid is not None:
                        M = Quaternion((qw, qx, qy, qz)).to_matrix().to_4x4()
                        M2 = A @ M @ A.inverted()
                        qdirection = M2.to_quaternion()
                        tile_data[(tile_x, tile_y, uid)] = [
                            uid,
                            tile_x,
                            tile_y,
                            file_name,
                            position,
                            qdirection,
                            track_nr_lookup[(tile_x, tile_y, uid)],
                        ]
    for mast_entry in MASTS:
        tile_x = mast_entry[1]
        tile_y = mast_entry[2]
        uid = mast_entry[0]
        key = (tile_x, tile_y, uid)
        if key in tile_data:
            mast_data.append(tile_data[key])
    return mast_data


def calculate_mast_wire_positions():
    return_mast_points = []
    mast_data = read_mast_data()
    for i, mast_entry in enumerate(mast_data):
        mast_tile = Vector((mast_entry[1], mast_entry[2]))
        mast_position = calculate_blender_coordinates(mast_entry[4], mast_tile)
        mast_rotation = mast_entry[5]
        mast_type_key = mast_entry[3]
        track_nr = mast_entry[6]
        if mast_type_key not in MAST_TYPES:
            print(f"Warning: Invalid mast type '{mast_type_key}'. Skipping mast.")
            continue
        if track_nr >= len(MAST_TYPES[mast_type_key]):
            print(f"Warning: Invalid track nr '{track_nr}' for type '{mast_type_key}'. Skipping mast.")
            continue
        mast_definition = MAST_TYPES[mast_type_key][track_nr]
        mast_forward = mast_rotation @ Vector((1, 0, 0))
        mast_right = mast_rotation @ Vector((0, 1, 0))
        mast_up = mast_rotation @ Vector((0, 0, 1))
        return_local = Vector((
            mast_definition["return_offset"].x,
            0.0,
            mast_definition["return_offset"].y
        ))
        return_point = mast_position + (
            mast_right * return_local.x +
            mast_forward * return_local.y +
            mast_up * return_local.z
        )
        return_mast_points.append(return_point)
    return return_mast_points


def make_return_wire():
    """
    Generates the mesh for the return overhead wire.

    The wire path is determined by attachment points defined in the global MASTS list
    and interpolated along the main curve_points. Sag is applied based on a
    ratio of the span length for each segment.

    Returns:
        bpy.types.Object: The created Blender object for the return wire, or None if no masts are defined.
    """
    return_wire_attachment_points = calculate_mast_wire_positions()
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


make_return_wire()
