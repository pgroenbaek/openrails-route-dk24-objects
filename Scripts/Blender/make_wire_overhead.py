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

TOP_WIRE_SPAN_RESOLUTION = 6
TOP_WIRE_SAG_CLEARANCE = 0.4
TOP_WIRE_SAG_HEIGHT = 0.3

CONNECTOR_DISTANCE_METERS = 10.0
CONNECTOR_RADIUS = 0.005
CONNECTOR_COLLAR_RADIUS = CONNECTOR_RADIUS * 1.33
CONNECTOR_COLLAR_LENGTH = 0.03
CONNECTOR_NUM_SIDES = 3

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

PROFILE_TOP_WIRE = [
    (Vector((0.0000, -0.0100)), Vector((0.0, 0.0273))),
    (Vector((0.0060, 0.0000)), Vector((0.0, 0.0508))),
    (Vector((-0.0060, 0.0000)), Vector((0.0, 0.0391))),
]
PROFILE_BOTTOM_WIRE = [
    (Vector((0.0000, 0.0101)), Vector((0.0, 0.0508))),
    (Vector((0.0060, 0.0000)), Vector((0.0, 0.0273))),
    (Vector((-0.0060, 0.0000)), Vector((0.0, 0.0391))),
]

MAST_TYPES = {
    "PGA_DKGantry_N1t6m_KL.s": [
        {"top_offset": Vector((0.0, 0.0, 7.3696)), "bottom_offset": Vector((0.0, 0.0, 6.1999))},
    ],
    "PGA_DKGantry_N1t6m_KR.s": [
        {"top_offset": Vector((0.0, 0.0, 7.3696)), "bottom_offset": Vector((0.0, 0.0, 6.1999))},
    ],
    "PGA_DKGantry_N1t6m_LL.s": [
        {"top_offset": Vector((0.0, 0.0, 7.3696)), "bottom_offset": Vector((0.0, 0.0, 6.1999))},
    ],
    "PGA_DKGantry_N1t6m_LR.s": [
        {"top_offset": Vector((0.0, 0.0, 7.3696)), "bottom_offset": Vector((0.0, 0.0, 6.1999))},
    ],
    "PGA_DKGantry_N2t6m_K.s": [
        {"top_offset": Vector((2.5, 0.0, 7.3696)), "bottom_offset": Vector((2.5, 0.0, 6.1999))},
        {"top_offset": Vector((-2.5, 0.0, 7.3696)), "bottom_offset": Vector((-2.5, 0.0, 6.1999))},
    ],
    "PGA_DKGantry_N2t6m_L.s": [
        {"top_offset": Vector((2.5, 0.0, 7.3696)), "bottom_offset": Vector((2.5, 0.0, 6.1999))},
        {"top_offset": Vector((-2.5, 0.0, 7.3696)), "bottom_offset": Vector((-2.5, 0.0, 6.1999))},
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
    Calculates the 3D attachment points for top and bottom wires on masts.

    This function reads mast data, transforms their game world positions
    and orientations to Blender coordinates, and then applies specific
    offsets defined in `MAST_TYPES` to determine the exact attachment
    points for both the top and bottom wires.

    Args:
        masts (list): A list of mast entries, where each entry is
                      [UiD, TileX, TileY, offset_index].

    Returns:
        tuple: A tuple containing two lists of `mathutils.Vector` objects:
               - `top_mast_points`: 3D points in Blender's coordinate system
                                    where the top wire should attach.
               - `bottom_mast_points`: 3D points in Blender's coordinate system
                                       where the bottom wire should attach.
    """
    top_mast_points = []
    bottom_mast_points = []
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
        top_local = Vector((
            mast_definition["top_offset"].y,
            mast_definition["top_offset"].x,
            mast_definition["top_offset"].z
        ))
        bottom_local = Vector((
            mast_definition["bottom_offset"].y,
            mast_definition["bottom_offset"].x,
            mast_definition["bottom_offset"].z
        ))
        top_point = mast_position + (
            mast_right * top_local.x +
            mast_forward * top_local.y +
            mast_up * top_local.z
        )
        bottom_point = mast_position + (
            mast_right * bottom_local.x +
            mast_forward * bottom_local.y +
            mast_up * bottom_local.z
        )
        top_mast_points.append(top_point)
        bottom_mast_points.append(bottom_point)
    return top_mast_points, bottom_mast_points


def get_polyline_length(polyline_points):
    """
    Calculates the total length of a polyline defined by a list of points.

    Args:
        polyline_points (List[Vector]): List of points defining the polyline.

    Returns:
        float: The total length of the polyline. Returns 0.0 if less than 2 points.
    """
    total_length = 0.0
    for i in range(len(polyline_points) - 1):
        total_length += (polyline_points[i + 1] - polyline_points[i]).length
    return total_length


def get_point_on_polyline_by_distance(polyline_points, target_distance):
    """
    Evaluates a point on a polyline at a specified distance from its start.

    Args:
        polyline_points (List[Vector]): List of points defining the polyline.
        target_distance (float): The distance from the start of the polyline
                                 at which to find the point.

    Returns:
        Vector: The 3D point on the polyline at the target_distance.
                Returns the last point if target_distance exceeds total length.
                Returns the first point if target_distance is 0 or less.
                Returns None if polyline_points is empty.
    """
    if not polyline_points:
        return None
    if target_distance <= 0:
        return polyline_points[0].copy()
    current_length = 0.0
    for i in range(len(polyline_points) - 1):
        p1 = polyline_points[i]
        p2 = polyline_points[i + 1]
        segment_vector = p2 - p1
        segment_length = segment_vector.length
        if current_length + segment_length >= target_distance:
            remaining_distance_in_segment = target_distance - current_length
            if segment_length == 0:
                return p1.copy()
            interpolation_factor = remaining_distance_in_segment / segment_length
            return p1.lerp(p2, interpolation_factor)
        current_length += segment_length
    return polyline_points[-1].copy()


def build_top_wire(name, top_mast_points, bottom_mast_points):
    """
    Generates a 3D mesh for the top overhead wire in Blender.

    The top wire path is calculated with sag based on `TOP_WIRE_SAG_HEIGHT`
    and adjusted to maintain a minimum clearance from the interpolated
    bottom wire path using `TOP_WIRE_SAG_CLEARANCE`. A new Blender mesh
    object is created, linked to the scene, and assigned a material.

    Args:
        name (str): The base name for the Blender object and mesh (e.g., "Track1").
        top_mast_points (list): A list of `mathutils.Vector` objects defining
                                the attachment points for the top wire on masts.
        bottom_mast_points (list): A list of `mathutils.Vector` objects used
                                   as a reference for minimum sag clearance.

    Returns:
        list: A list of `mathutils.Vector` objects representing the actual
              3D path points of the generated top wire.
    """
    top_wire_points = []
    mesh_vertices = []
    mesh_uvs = []
    mesh_faces = []
    profile_point_count = len(PROFILE_TOP_WIRE)
    for segment_index in range(len(top_mast_points) - 1):
        start_top_point, end_top_point = top_mast_points[segment_index], top_mast_points[segment_index + 1]
        start_bottom_point, end_bottom_point = bottom_mast_points[segment_index], bottom_mast_points[segment_index + 1]
        for span_index in range(TOP_WIRE_SPAN_RESOLUTION + 1):
            interpolation_factor = span_index / TOP_WIRE_SPAN_RESOLUTION
            interpolated_top_x = start_top_point.x * (1 - interpolation_factor) + end_top_point.x * interpolation_factor
            interpolated_top_y = start_top_point.y * (1 - interpolation_factor) + end_top_point.y * interpolation_factor
            interpolated_top_base_z = start_top_point.z * (1 - interpolation_factor) + end_top_point.z * interpolation_factor
            arch_factor = 4 * interpolation_factor * (1 - interpolation_factor)
            sag_amount = TOP_WIRE_SAG_HEIGHT * arch_factor
            interpolated_top_z = interpolated_top_base_z - sag_amount
            interpolated_bottom_point = Vector((
                start_bottom_point.x * (1 - interpolation_factor) + end_bottom_point.x * interpolation_factor,
                start_bottom_point.y * (1 - interpolation_factor) + end_bottom_point.y * interpolation_factor,
                start_bottom_point.z * (1 - interpolation_factor) + end_bottom_point.z * interpolation_factor,
            ))
            minimum_allowed_z = interpolated_bottom_point.z + TOP_WIRE_SAG_CLEARANCE
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
            for profile_offset, texcoord in PROFILE_TOP_WIRE:
                mesh_vertices.append(
                    wire_point +
                    right_vector * profile_offset.x +
                    upward_vector * profile_offset.y
                )
                mesh_uvs.append(texcoord)
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
    mesh = bpy.data.meshes.new(f"{name}_TopWire")
    obj = bpy.data.objects.new(f"{name}_TopWire", mesh)
    bpy.context.collection.objects.link(obj)
    material = bpy.data.materials.get(MATERIAL_NAME)
    if material is None:
        material = bpy.data.materials.new(MATERIAL_NAME)
    if material.name not in obj.data.materials:
        obj.data.materials.append(material)
    material_index = obj.data.materials.find(material.name)
    mesh.from_pydata(mesh_vertices, [], mesh_faces)
    mesh.update()
    for poly in mesh.polygons:
        poly.use_smooth = True
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(180))
    mesh.polygons.foreach_set("material_index", [material_index] * len(mesh.polygons))
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = mesh_uvs[vertex_index]
    return top_wire_points


def build_bottom_wire(name, top_mast_points, bottom_mast_points):
    """
    Generates a 3D mesh for the bottom overhead wire in Blender.

    The bottom wire path is created directly from the provided `bottom_mast_points`.
    A new Blender mesh object is created, linked to the scene, and assigned a material.

    Args:
        name (str): The base name for the Blender object and mesh (e.g., "Track1").
        top_mast_points (list): A list of `mathutils.Vector` objects used to determine
                                the upward direction for proper wire orientation.
        bottom_mast_points (list): A list of `mathutils.Vector` objects defining
                                   the attachment points for the bottom wire on masts,
                                   which also serve as its path points.

    Returns:
        list: A list of `mathutils.Vector` objects representing the actual
              3D path points of the generated bottom wire.
    """
    bottom_wire_points = []
    mesh_vertices = []
    mesh_uvs = []
    mesh_faces = []
    profile_point_count = len(PROFILE_BOTTOM_WIRE)
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
        for profile_offset, texcoord in PROFILE_BOTTOM_WIRE:
            mesh_vertices.append(
                mast_position +
                right_vector * profile_offset.x +
                upward_vector * profile_offset.y
            )
            mesh_uvs.append(texcoord)
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
    mesh = bpy.data.meshes.new(f"{name}_BottomWire")
    obj = bpy.data.objects.new(f"{name}_BottomWire", mesh)
    bpy.context.collection.objects.link(obj)
    material = bpy.data.materials.get(MATERIAL_NAME)
    if material is None:
        material = bpy.data.materials.new(MATERIAL_NAME)
    if material.name not in obj.data.materials:
        obj.data.materials.append(material)
    material_index = obj.data.materials.find(material.name)
    mesh.from_pydata(mesh_vertices, [], mesh_faces)
    mesh.update()
    for poly in mesh.polygons:
        poly.use_smooth = True
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(180))
    mesh.polygons.foreach_set("material_index", [material_index] * len(mesh.polygons))
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = mesh_uvs[vertex_index]
    return bottom_wire_points


def build_connectors(name, top_wire_points, bottom_wire_points):
    """
    Generates a 3D mesh for the connectors (droppers) between the top and bottom wires in Blender.

    Connectors are placed at regular `CONNECTOR_DISTANCE_METERS` intervals along
    the `top_wire_points` path. Each connector consists of a central shaft and
    collars at its ends, connecting the top wire to its nearest projected point
    on the bottom wire. A new Blender mesh object is created, linked to the scene,
    and assigned a material.

    Args:
        name (str): The base name for the Blender object and mesh (e.g., "Track1").
        top_wire_points (list): A list of `mathutils.Vector` objects defining
                                the path of the top overhead wire.
        bottom_wire_points (list): A list of `mathutils.Vector` objects defining
                                   the path of the bottom overhead wire.

    Returns:
        None: This function creates and links objects directly within Blender.
    """
    mesh_vertices = []
    mesh_uvs = []
    mesh_faces = []
    shaft_face_indices = []
    total_top_wire_length = get_polyline_length(top_wire_points)
    current_distance = 0.0
    while current_distance <= total_top_wire_length + 1e-6:
        top_point = get_point_on_polyline_by_distance(top_wire_points, current_distance)
        current_distance += CONNECTOR_DISTANCE_METERS
        if top_point is None: 
            continue
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
                if side_index == 0:
                    mesh_uvs.append(Vector((0.0, 0.0273)))
                elif side_index == CONNECTOR_NUM_SIDES - 1:
                    mesh_uvs.append(Vector((0.0, 0.0508)))
                else:
                    mesh_uvs.append(Vector((0.0, 0.0391)))
        for side_index in range(CONNECTOR_NUM_SIDES):
            next_side_index = (side_index + 1) % CONNECTOR_NUM_SIDES
            face_index = len(mesh_faces)
            mesh_faces.append((
                base_vertex_index + side_index,
                base_vertex_index + next_side_index,
                base_vertex_index + CONNECTOR_NUM_SIDES + next_side_index,
                base_vertex_index + CONNECTOR_NUM_SIDES + side_index
            ))
            shaft_face_indices.append(face_index)
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
                mesh_uvs.append(Vector((0.0, 1.0)))
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
                mesh_uvs.append(Vector((0.0, 1.0)))
        for side_index in range(CONNECTOR_NUM_SIDES):
            next_side_index = (side_index + 1) % CONNECTOR_NUM_SIDES
            mesh_faces.append((
                base_vertex_index + side_index,
                base_vertex_index + next_side_index,
                base_vertex_index + CONNECTOR_NUM_SIDES + next_side_index,
                base_vertex_index + CONNECTOR_NUM_SIDES + side_index
            ))
    mesh = bpy.data.meshes.new(f"{name}_Connectors")
    obj = bpy.data.objects.new(f"{name}_Connectors", mesh)
    bpy.context.collection.objects.link(obj)
    material = bpy.data.materials.get(MATERIAL_NAME)
    if material is None:
        material = bpy.data.materials.new(MATERIAL_NAME)
    if material.name not in obj.data.materials:
        obj.data.materials.append(material)
    material_index = obj.data.materials.find(material.name)
    mesh.from_pydata(mesh_vertices, [], mesh_faces)
    mesh.update()
    for face_index in shaft_face_indices:
        if face_index < len(mesh.polygons):
            mesh.polygons[face_index].use_smooth = True
    mesh.polygons.foreach_set("material_index", [material_index] * len(mesh.polygons))
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = mesh_uvs[vertex_index]


def make_overhead_wire():
    """
    Main function to generate overhead catenary wire system in Blender.

    This function iterates through the `MASTS` dictionary, calculating
    the attachment points for the top and bottom wires for each defined
    track. It then proceeds to build the mesh for the top wire (with sag),
    the bottom wire, and the connectors that link them, creating corresponding
    Blender objects.
    """
    for name, masts in MASTS.items():
        top_mast_points, bottom_mast_points = calculate_mast_wire_positions(masts)
        top_wire_points = build_top_wire(name, top_mast_points, bottom_mast_points)
        bottom_wire_points = build_bottom_wire(name, top_mast_points, bottom_mast_points)
        build_connectors(name, top_wire_points, bottom_wire_points)


make_overhead_wire()



