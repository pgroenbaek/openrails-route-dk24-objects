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
from pathlib import Path
from math import sin, cos, pi
from mathutils import Vector, Quaternion, Matrix

MATERIAL_NAME = "Wire"

WIRE_NAME = "ReturnWire"
WIRE_SPAN_RESOLUTION = 6
WIRE_THICKNESS = 0.03
WIRE_SAG_RATIO = 0.011

WORLD_UP = Vector((0, 0, 1))
#WORLD_FOLDER = "/media/peter/T7 Shield/Repos/personal/openrails-route-dk24/ROUTES/OR_DK24/WORLD"
WORLD_FOLDER = "D:\Games\Open Rails\Content\PGA DK24\ROUTES\OR_DK24\WORLD"

TILE_SIZE = 2048

# This position and tile is where to place the generated object in world coordinates.
# Rotation of the object should be QDirection( 0 0 0 1 ).
REFERENCE_POSITION_X = -874.908
REFERENCE_POSITION_Y = 14.4113
REFERENCE_POSITION_Z = -828.282
REFERENCE_TILE_X = -5656
REFERENCE_TILE_Y = 15119

PROFILE_WIRE = [
    (Vector((0.0,  WIRE_THICKNESS / 2.0)), Vector((0.0, 0.00))),
    (Vector((WIRE_THICKNESS / 2.0, 0.0)), Vector((0.0, 0.08))),
    (Vector((0.0, -(WIRE_THICKNESS / 2.0))), Vector((0.0, 0.00))),
    (Vector((-(WIRE_THICKNESS / 2.0), 0.0)), Vector((0.0, 0.08))),
]

MAST_TYPES = {
    "PGA_DKGantry_N1t6m_KL.s": [
        {"offset": Vector((-2.799, 0.0, 6.98))},
    ],
    "PGA_DKGantry_N1t6m_KR.s": [
        {"offset": Vector((2.799, 0.0, 6.98))},
    ],
    "PGA_DKGantry_N1t6m_LL.s": [
        {"offset": Vector((-2.799, 0.0, 6.98))},
    ],
    "PGA_DKGantry_N1t6m_LR.s": [
        {"offset": Vector((2.799, 0.0, 6.98))},
    ],
    "PGA_DKGantry_N2t6m_K.s": [
        {"offset": Vector((5.299, 0.0, 6.98))},
        {"offset": Vector((-5.299, 0.0, 6.98))},
    ],
    "PGA_DKGantry_N2t6m_L.s": [
        {"offset": Vector((5.299, 0.0, 6.98))},
        {"offset": Vector((-5.299, 0.0, 6.98))},
    ],
}

MASTS = {
    "Track1": [
        #UiD, TileX, TileY, offset_index (for the corresponding shape within MAST_TYPES)
        [6955, -5656, 15119, 0],
        [6956, -5656, 15119, 0],
        [6958, -5656, 15119, 0],
        [6959, -5656, 15119, 0],
        [6960, -5656, 15119, 0],
        [6961, -5656, 15119, 0],
        [112, -5657, 15119, 0],
        [113, -5657, 15119, 0],
        [3231, -5657, 15118, 0],
        [3232, -5657, 15118, 0],
        [3241, -5657, 15118, 0],
        [3245, -5657, 15118, 0],
        [3243, -5657, 15118, 0],
        [3233, -5657, 15118, 0],
        [3234, -5657, 15118, 0],
        [3253, -5657, 15118, 0],
        [3254, -5657, 15118, 0],
    ],
    "Track2": [
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
    ],
}


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


def read_mast_data(masts):
    """
    Reads mast data from world files based on provided mast entries.

    This function iterates through the `masts` list, extracts unique tile
    coordinates and UIDs, then reads the corresponding world files to
    find the position, rotation, and shape name for each specified mast.

    Args:
        masts (list): A list of mast entries, where each entry is
                      [UiD, TileX, TileY, offset_index].

    Returns:
        list: A list of processed mast data entries, each containing:
              [uid, tile_x, tile_y, file_name, position, qdirection, offset_index].
              Returns an empty list if no valid mast data is found.
    """
    mast_data = []
    tiles_to_uids = {}
    offset_index_lookup = {}
    for mast_entry in masts:
        uid = mast_entry[0]
        tile_x = mast_entry[1]
        tile_y = mast_entry[2]
        offset_index = mast_entry[3]
        key = (tile_x, tile_y, uid)
        if key not in offset_index_lookup:
            offset_index_lookup[key] = offset_index
        key = (tile_x, tile_y)
        if key not in tiles_to_uids:
            tiles_to_uids[key] = set()
        tiles_to_uids[key].add(uid)
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
        qdirection = None
        in_static = False
        lines = file_path.read_text(encoding="utf-16-le", errors="ignore").splitlines()
        for line in lines:
            line = line.strip()
            if line.startswith("Static"):
                uid = None
                file_name = None
                position = None
                qdirection = None
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
                        qdirection = Quaternion((qw, qx, qz, qy))
                        qdirection.normalize()
                elif ")" in line:
                    in_static = False
                    if uid in tiles_to_uids[(tile_x, tile_y)] and uid is not None:
                        tile_data[(tile_x, tile_y, uid)] = [
                            uid,
                            tile_x,
                            tile_y,
                            file_name,
                            position,
                            qdirection,
                            offset_index_lookup[(tile_x, tile_y, uid)],
                        ]
    for mast_entry in masts:
        tile_x = mast_entry[1]
        tile_y = mast_entry[2]
        uid = mast_entry[0]
        key = (tile_x, tile_y, uid)
        if key in tile_data:
            mast_data.append(tile_data[key])
    return mast_data


def calculate_mast_wire_positions(masts):
    """
    Calculates the 3D attachment points for wires on masts.

    This function reads mast data, transforms their game world positions
    and orientations to Blender coordinates, and then applies specific
    offsets defined in `MAST_TYPES` to determine the exact attachment
    points for the wires.

    Args:
        masts (list): A list of mast entries, where each entry is
                      [UiD, TileX, TileY, offset_index].

    Returns:
        list: A list of `mathutils.Vector` objects, each representing a
              3D point in Blender's coordinate system where a wire should attach.
    """
    return_mast_points = []
    mast_data = read_mast_data(masts)
    for i, mast_entry in enumerate(mast_data):
        mast_tile = Vector((mast_entry[1], mast_entry[2]))
        mast_position = calculate_blender_coordinates(mast_entry[4], mast_tile)
        mast_rotation = mast_entry[5]
        mast_type_key = mast_entry[3]
        offset_index = mast_entry[6]
        if mast_type_key not in MAST_TYPES:
            print(f"Warning: Invalid mast type '{mast_type_key}'. Skipping mast.")
            continue
        if offset_index >= len(MAST_TYPES[mast_type_key]):
            print(f"Warning: Invalid offset index '{offset_index}' for type '{mast_type_key}'. Skipping mast.")
            continue
        mast_definition = MAST_TYPES[mast_type_key][offset_index]
        mast_forward = mast_rotation @ Vector((1, 0, 0))
        mast_right = mast_rotation @ Vector((0, 1, 0))
        mast_up = mast_rotation @ Vector((0, 0, 1))
        return_local = Vector((
            mast_definition["offset"].y,
            mast_definition["offset"].x,
            mast_definition["offset"].z
        ))
        return_point = mast_position + (
            mast_right * return_local.x +
            mast_forward * return_local.y +
            mast_up * return_local.z
        )
        return_mast_points.append(return_point)
    return return_mast_points


def build_wire(name, wire_attachment_points):
    """
    Generates a 3D wire mesh in Blender based on a series of attachment points.

    The wire is constructed by creating segments between consecutive attachment points,
    applying a sag profile, and then extruding a 2D profile along the resulting path.
    A new Blender mesh object is created, linked to the scene, and assigned a material.

    Args:
        name (str): The base name for the Blender object and mesh (e.g., "Track1").
        wire_attachment_points (list): A list of `mathutils.Vector` objects defining
                                       the start and end points of each wire span.

    Returns:
        None: This function creates and links objects directly within Blender.
    """
    return_wire_path_points = []
    for segment_index in range(len(wire_attachment_points) - 1):
        start_point = wire_attachment_points[segment_index]
        end_point = wire_attachment_points[segment_index + 1]
        span_length = (end_point - start_point).length
        max_sag_for_this_span = span_length * WIRE_SAG_RATIO
        for span_sub_index in range(WIRE_SPAN_RESOLUTION + 1):
            interpolation_factor = span_sub_index / WIRE_SPAN_RESOLUTION
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
    profile_point_count = len(PROFILE_WIRE)
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
        if right_vector.length_squared < 1e-12:
            right_vector = Vector((1, 0, 0)).cross(segment_direction)
        right_vector.normalize()
        upward_vector = right_vector.cross(segment_direction).normalized()
        base_vertex_index = len(mesh_vertices)
        for profile_offset, texcoord in PROFILE_WIRE:
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
    mesh = bpy.data.meshes.new(f"{name}_{WIRE_NAME}")
    obj = bpy.data.objects.new(f"{name}_{WIRE_NAME}", mesh)
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


def make_wire():
    """
    Main function to create wire objects in Blender.

    This function iterates through the `MASTS` dictionary, calculating
    the attachment points for each defined track and then constructing
    the corresponding wire mesh in Blender.
    """
    for name, masts in MASTS.items():
        wire_attachment_points = calculate_mast_wire_positions(masts)
        build_wire(name, wire_attachment_points)


make_wire()
