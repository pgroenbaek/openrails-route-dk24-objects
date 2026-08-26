#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

# This is a Blender Python script.
#
# It is called by `run_operations.py`, which reads the human-readable
# JSON configuration and dispatches the requested Blender operations.
# The `run_operations.py` script can also be run directly from Blender's
# Scripting Console configured with a set of config files.

import bpy
import math
from pathlib import Path
from math import sin, cos, pi
from mathutils import Vector, Quaternion, Matrix


MATERIAL_NAME = "Wire"
MATERIAL_MSTS_TEXTURE_NAME = "DB_Rails1.png"
LOD_DISTANCE_METERS = 500

TOP_WIRE_SPAN_RESOLUTION = 6
TOP_WIRE_SAG_CLEARANCE = 0.4
TOP_WIRE_SAG_HEIGHT = 0.26

CONNECTOR_DISTANCE_METERS = 10.0
CONNECTOR_RADIUS = 0.005
CONNECTOR_COLLAR_RADIUS = CONNECTOR_RADIUS * 1.33
CONNECTOR_COLLAR_LENGTH = 0.03
CONNECTOR_NUM_SIDES = 3

WORLD_UP = Vector((0, 0, 1))
WORLD_FOLDER = "/media/peter/T7 Shield/ORTS/Content/PGA DK24/ROUTES/OR_DK24/WORLD"

TILE_SIZE = 2048

REFERENCE_POSITION = Vector((-874.908, 14.4113, -828.282))
REFERENCE_TILE = Vector((-5656, 15119))

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


def get_collection(collection, name):
    """
    Recursively searches for a collection by name within a given collection and its children.

    Args:
        collection (bpy.types.Collection): The starting collection to search within.
        name (str): The name of the collection to find.

    Returns:
        bpy.types.Collection or None: The found collection, or None if not found.
    """
    for c in collection.children:
        if c.name == name:
            return c

    return None


def link_object_to_lod_collection(obj, lod_distance, main_collection_name="MAIN"):
    """
    Links an object to the appropriate LOD collection based on the distance level.

    Args:
        obj (bpy.types.Object): Blender object to link.
        lod_distance (float): LOD distance in meters.
        main_collection_name (str): The name of the main collection to group LODs under.
    """
    main_collection = get_collection(bpy.context.scene.collection, main_collection_name)

    if main_collection is None:
        main_collection = bpy.data.collections.new(main_collection_name)
        bpy.context.scene.collection.children.link(main_collection)

    dlevel_collection_name = f"MAIN_{int(lod_distance):04d}"
    dlevel_collection = get_collection(main_collection, dlevel_collection_name)

    if dlevel_collection is None:
        dlevel_collection = bpy.data.collections.new(dlevel_collection_name)
        main_collection.children.link(dlevel_collection)

    dlevel_collection.objects.link(obj)


def set_exporter_texture_name(material, texture_name):
    """
    Sets the texture name used for a material with the MSTS/ORTS exporter if
    it is not already set.

    Args:
        material (bpy.types.Material): Blender material to configure.
        texture_name (str): Texture name to use for the material.
    """
    if hasattr(material, "msts") and hasattr(material.msts, "BaseColorFilepath"):
        if not material.msts.BaseColorFilepath:
            material.msts.BaseColorFilepath = texture_name


def assign_material(obj, material_name):
    """
    Assigns a material to an object's mesh. The material is created if it
    does not already exist.

    Args:
        obj (bpy.types.Object): Blender object receiving the material.
        material_name (str): Name of the material to create or retrieve.

    Returns:
        bpy.types.Material: The assigned material.
    """
    material = bpy.data.materials.get(material_name)

    if material is None:
        material = bpy.data.materials.new(material_name)

    if material.name not in obj.data.materials:
        obj.data.materials.append(material)

    return material


def calculate_blender_coordinates(position, tile_coords, tile_size, reference_position, reference_tile):
    """
    Calculates Blender coordinates based on position, tile coordinates, and a reference point.

    Args:
        position (Vector): The current position in game world coordinates (x, y, z).
        tile_coords (Vector): The tile coordinates (tile_x, tile_y) for the current position.
        tile_size (int): The size of a tile in world units.
        reference_position (Vector): The reference position in game world coordinates (x, y, z).
        reference_tile (Vector): The reference tile coordinates (tile_x, tile_y).

    Returns:
        Vector: The corresponding 3D point in Blender's coordinate system.
    """
    blender_x = (tile_coords.x - reference_tile.x) * tile_size + (position.x - reference_position.x)
    blender_y = (tile_coords.y - reference_tile.y) * tile_size + (position.z - reference_position.z)
    blender_z = position.y - reference_position.y

    return Vector((blender_x, blender_y, blender_z))


def read_mast_data(masts_config, world_folder):
    """
    Reads mast data from world files based on provided mast entries.

    This function iterates through the `masts_config` list, extracts unique tile
    coordinates and UIDs, then reads the corresponding world files to
    find the position, rotation, and shape name for each specified mast.

    Args:
        masts_config (list): A list of mast entries, where each entry is
                      [UiD, TileX, TileY, offset_index].
        world_folder (str): The path to the world files directory.

    Returns:
        list: A list of processed mast data entries, each containing:
              [uid, tile_x, tile_y, file_name, position, qdirection, offset_index].
              Returns an empty list if no valid mast data is found.
    """
    mast_data = []
    tiles_to_uids = {}
    offset_index_lookup = {}
    for mast_entry in masts_config:
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
        filename = "w{:+07d}{:+07d}.w".format(int(tile_x), int(tile_y))
        file_path = Path(world_folder) / filename

        if not file_path.exists():
            print(f"Warning: Missing world file {filename}")
            continue

        uid = None
        file_name = None
        position = None
        qdirection = None
        in_static = False
        in_gantry = False
        lines = file_path.read_text(encoding="utf-16-le", errors="ignore").splitlines()

        for line in lines:
            line = line.strip()

            if line.startswith("Static ("):
                uid = None
                file_name = None
                position = None
                qdirection = None
                in_static = True
                in_gantry = False
                continue

            if line.startswith("Gantry ("):
                uid = None
                file_name = None
                position = None
                qdirection = None
                in_static = False
                in_gantry = True
                continue

            if in_static or in_gantry:
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

                elif line.startswith("Matrix3x3"):
                    continue

                elif line.startswith("VDbId"):
                    continue

                elif line.startswith("StaticFlags"):
                    continue

                elif line.startswith("StaticDetailLevel"):
                    continue

                elif ")" in line:
                    in_static = False
                    in_gantry = False
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

    for mast_entry in masts_config:
        tile_x = mast_entry[1]
        tile_y = mast_entry[2]
        uid = mast_entry[0]
        key = (tile_x, tile_y, uid)

        if key in tile_data:
            mast_data.append(tile_data[key])

    return mast_data


def calculate_mast_wire_positions(masts_config, mast_types, tile_size, reference_position, reference_tile, world_folder):
    """
    Calculates the 3D attachment points for top and bottom wires on masts.

    This function reads mast data, transforms their game world positions
    and orientations to Blender coordinates, and then applies specific
    offsets defined in `mast_types` to determine the exact attachment
    points for both the top and bottom wires.

    Args:
        masts_config (list): A list of mast entries, where each entry is
                      [UiD, TileX, TileY, offset_index].
        mast_types (dict): A dictionary defining mast types and their offsets.
        tile_size (int): The size of a tile in world units.
        reference_position (Vector): The reference position in game world coordinates (x, y, z).
        reference_tile (Vector): The reference tile coordinates (tile_x, tile_y).
        world_folder (str): The path to the world files directory.

    Returns:
        tuple: A tuple containing two lists of `mathutils.Vector` objects:
               - `top_mast_points`: 3D points in Blender's coordinate system
                                    where the top wire should attach.
               - `bottom_mast_points`: 3D points in Blender's coordinate system
                                       where the bottom wire should attach.
    """
    top_mast_points = []
    bottom_mast_points = []
    mast_data = read_mast_data(masts_config, world_folder)

    for i, mast_entry in enumerate(mast_data):
        mast_tile = Vector((mast_entry[1], mast_entry[2]))
        mast_position = calculate_blender_coordinates(mast_entry[4], mast_tile, tile_size, reference_position, reference_tile)
        mast_rotation = mast_entry[5]
        mast_type_key = mast_entry[3]
        offset_index = mast_entry[6]

        if mast_type_key not in mast_types:
            print(f"Warning: Mast type '{mast_type_key}' from entry {mast_entry} not defined in mast_types. Skipping mast.")
            continue

        if offset_index >= len(mast_types[mast_type_key]):
            print(f"Warning: Invalid offset index '{offset_index}' for type '{mast_type_key}'. Skipping mast.")
            continue

        mast_definition = mast_types[mast_type_key][offset_index]
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


def build_top_wire(name, top_mast_points, bottom_mast_points, lod_distance_meters, material_name, material_msts_texture_name, world_up, top_wire_span_resolution, top_wire_sag_clearance, top_wire_sag_height, profile_top_wire):
    """
    Generates a 3D mesh for the top overhead wire in Blender.

    The top wire path is calculated with sag based on `top_wire_sag_height`
    and adjusted to maintain a minimum clearance from the interpolated
    bottom wire path using `top_wire_sag_clearance`. A new Blender mesh
    object is created, linked to the scene, and assigned a material.

    Args:
        name (str): The base name for the Blender object and mesh (e.g., "Track1").
        top_mast_points (list): A list of `mathutils.Vector` objects defining
                                the attachment points for the top wire on masts.
        bottom_mast_points (list): A list of `mathutils.Vector` objects used
                                   as a reference for minimum sag clearance.
        lod_distance_meters (float): LOD distance in meters for collection linking.
        material_name (str): Name of the material to create or retrieve.
        material_msts_texture_name (str): Texture name to use for the material exporter.
        world_up (Vector): World up direction used when generating the wire geometry.
        top_wire_span_resolution (int): Number of segments per wire span.
        top_wire_sag_clearance (float): Minimum clearance between top and bottom wire.
        top_wire_sag_height (float): Maximum sag height for the top wire.
        profile_top_wire (list): Profile definition for the top wire cross-section.

    Returns:
        list: A list of `mathutils.Vector` objects representing the actual
              3D path points of the generated top wire.
    """
    top_wire_points = []
    mesh_vertices = []
    mesh_uvs = []
    mesh_faces = []
    profile_point_count = len(profile_top_wire)

    for segment_index in range(len(top_mast_points) - 1):
        start_top_point, end_top_point = top_mast_points[segment_index], top_mast_points[segment_index + 1]
        start_bottom_point, end_bottom_point = bottom_mast_points[segment_index], bottom_mast_points[segment_index + 1]

        for span_index in range(top_wire_span_resolution + 1):
            interpolation_factor = span_index / top_wire_span_resolution
            interpolated_top_x = start_top_point.x * (1 - interpolation_factor) + end_top_point.x * interpolation_factor
            interpolated_top_y = start_top_point.y * (1 - interpolation_factor) + end_top_point.y * interpolation_factor
            interpolated_top_base_z = start_top_point.z * (1 - interpolation_factor) + end_top_point.z * interpolation_factor
            arch_factor = 4 * interpolation_factor * (1 - interpolation_factor)
            sag_amount = top_wire_sag_height * arch_factor
            interpolated_top_z = interpolated_top_base_z - sag_amount
            interpolated_bottom_point = Vector((
                start_bottom_point.x * (1 - interpolation_factor) + end_bottom_point.x * interpolation_factor,
                start_bottom_point.y * (1 - interpolation_factor) + end_bottom_point.y * interpolation_factor,
                start_bottom_point.z * (1 - interpolation_factor) + end_bottom_point.z * interpolation_factor,
            ))
            minimum_allowed_z = interpolated_bottom_point.z + top_wire_sag_clearance

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
                upward_vector = world_up
            else:
                upward_vector.normalize()

            right_vector = segment_direction.cross(upward_vector)

            if right_vector.length == 0:
                right_vector = Vector((1, 0, 0))
            else:
                right_vector.normalize()

            upward_vector = right_vector.cross(segment_direction).normalized()
            base_vertex_index = len(mesh_vertices)

            for profile_offset, texcoord in profile_top_wire:
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
    
    if not top_wire_points:
        print("Warning: No path points generated for top wire. Skipping mesh creation.")
        return None
    
    mesh = bpy.data.meshes.new(f"{name}_TopWire")
    obj = bpy.data.objects.new(f"{name}_TopWire", mesh)

    link_object_to_lod_collection(obj, lod_distance_meters)

    material = assign_material(obj, material_name)
    material_index = obj.data.materials.find(material.name)

    set_exporter_texture_name(material, material_msts_texture_name)

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


def build_bottom_wire(name, top_mast_points, bottom_mast_points, lod_distance_meters, material_name, material_msts_texture_name, world_up, profile_bottom_wire):
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
        lod_distance_meters (float): LOD distance in meters for collection linking.
        material_name (str): Name of the material to create or retrieve.
        material_msts_texture_name (str): Texture name to use for the material exporter.
        world_up (Vector): World up direction used when generating the wire geometry.
        profile_bottom_wire (list): Profile definition for the bottom wire cross-section.

    Returns:
        list: A list of `mathutils.Vector` objects representing the actual
              3D path points of the generated bottom wire.
    """
    bottom_wire_points = []
    mesh_vertices = []
    mesh_uvs = []
    mesh_faces = []
    profile_point_count = len(profile_bottom_wire)

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
            upward_vector = world_up
        else:
            upward_vector.normalize()

        right_vector = segment_direction.cross(upward_vector)

        if right_vector.length == 0:
            right_vector = Vector((1, 0, 0))
        else:
            right_vector.normalize()

        upward_vector = right_vector.cross(segment_direction).normalized()
        base_vertex_index = len(mesh_vertices)

        for profile_offset, texcoord in profile_bottom_wire:
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
    
    if not bottom_wire_points:
        print("Warning: No path points generated for bottom wire. Skipping mesh creation.")
        return None

    mesh = bpy.data.meshes.new(f"{name}_BottomWire")
    obj = bpy.data.objects.new(f"{name}_BottomWire", mesh)

    link_object_to_lod_collection(obj, lod_distance_meters)

    material = assign_material(obj, material_name)
    material_index = obj.data.materials.find(material.name)

    set_exporter_texture_name(material, material_msts_texture_name)

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


def build_connectors(name, top_wire_points, bottom_wire_points, lod_distance_meters, material_name, material_msts_texture_name, world_up, connector_distance_meters, connector_radius, connector_collar_radius, connector_collar_length, connector_num_sides):
    """
    Generates a 3D mesh for the connectors (droppers) between the top and bottom wires in Blender.

    Connectors are placed at regular `connector_distance_meters` intervals along
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
        lod_distance_meters (float): LOD distance in meters for collection linking.
        material_name (str): Name of the material to create or retrieve.
        material_msts_texture_name (str): Texture name to use for the material exporter.
        world_up (Vector): World up direction used when generating the wire geometry.
        connector_distance_meters (float): Interval distance between connectors.
        connector_radius (float): Radius of the connector shaft.
        connector_collar_radius (float): Radius of the connector collars.
        connector_collar_length (float): Length of the connector collars.
        connector_num_sides (int): Number of sides for cylindrical connectors.

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
        current_distance += connector_distance_meters

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

        if connector_length <= connector_collar_length * 2.0:
            continue

        connector_direction = connector_axis.normalized()

        if abs(connector_direction.dot(world_up)) > 0.999:
            connector_right_vector = Vector((1, 0, 0))
        else:
            connector_right_vector = connector_direction.cross(world_up).normalized()
        
        connector_up_vector = connector_right_vector.cross(connector_direction).normalized()

        shaft_start_point = top_point + connector_direction * connector_collar_length
        shaft_end_point = best_projection_point - connector_direction * connector_collar_length

        base_vertex_index = len(mesh_vertices)

        for center_point in (shaft_start_point, shaft_end_point):
            for side_index in range(connector_num_sides):
                angle = 2.0 * pi * side_index / connector_num_sides
                mesh_vertices.append(
                    center_point + 
                    connector_right_vector * cos(angle) * connector_radius +
                    connector_up_vector * sin(angle) * connector_radius
                )
                if side_index == 0:
                    mesh_uvs.append(Vector((0.0, 0.0273)))
                elif side_index == connector_num_sides - 1:
                    mesh_uvs.append(Vector((0.0, 0.0508)))
                else:
                    mesh_uvs.append(Vector((0.0, 0.0391)))
        
        for side_index in range(connector_num_sides):
            next_side_index = (side_index + 1) % connector_num_sides
            face_index = len(mesh_faces)
            mesh_faces.append((
                base_vertex_index + side_index,
                base_vertex_index + next_side_index,
                base_vertex_index + connector_num_sides + next_side_index,
                base_vertex_index + connector_num_sides + side_index
            ))
            shaft_face_indices.append(face_index)
        
        collar_start_point = top_point
        collar_end_point = top_point + connector_direction * connector_collar_length

        base_vertex_index = len(mesh_vertices)

        for center_point in (collar_start_point, collar_end_point):
            for side_index in range(connector_num_sides):
                angle = 2.0 * pi * side_index / connector_num_sides
                mesh_vertices.append(
                    center_point + 
                    connector_right_vector * cos(angle) * connector_collar_radius + 
                    connector_up_vector * sin(angle) * connector_collar_radius
                )
                mesh_uvs.append(Vector((0.0, 1.0)))
        
        for side_index in range(connector_num_sides):
            next_side_index = (side_index + 1) % connector_num_sides
            mesh_faces.append((
                base_vertex_index + side_index,
                base_vertex_index + next_side_index,
                base_vertex_index + connector_num_sides + next_side_index,
                base_vertex_index + connector_num_sides + side_index
            ))

        collar_start_point = best_projection_point - connector_direction * connector_collar_length
        collar_end_point = best_projection_point

        base_vertex_index = len(mesh_vertices)

        for center_point in (collar_start_point, collar_end_point):
            for side_index in range(connector_num_sides):
                angle = 2.0 * pi * side_index / connector_num_sides
                mesh_vertices.append(
                    center_point + 
                    connector_right_vector * cos(angle) * connector_collar_radius + 
                    connector_up_vector * sin(angle) * connector_collar_radius
                )
                mesh_uvs.append(Vector((0.0, 1.0)))
        
        for side_index in range(connector_num_sides):
            next_side_index = (side_index + 1) % connector_num_sides
            mesh_faces.append((
                base_vertex_index + side_index,
                base_vertex_index + next_side_index,
                base_vertex_index + connector_num_sides + next_side_index,
                base_vertex_index + connector_num_sides + side_index
            ))
    
    mesh = bpy.data.meshes.new(f"{name}_Connectors")
    obj = bpy.data.objects.new(f"{name}_Connectors", mesh)

    link_object_to_lod_collection(obj, lod_distance_meters)

    material = assign_material(obj, material_name)
    material_index = obj.data.materials.find(material.name)

    set_exporter_texture_name(material, material_msts_texture_name)

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


def perform_operation(params):
    """
    Blender operation to generate overhead catenary wire system.

    Args:
        params (dict): A dictionary containing configuration parameters for the operation.
                        Expected keys include:
                        - "material_name" (str)
                        - "material_msts_texture_name" (str)
                        - "lod_distance_meters" (float)
                        - "top_wire_span_resolution" (int)
                        - "top_wire_sag_clearance" (float)
                        - "top_wire_sag_height" (float)
                        - "connector_distance_meters" (float)
                        - "connector_radius" (float)
                        - "connector_collar_radius" (float, optional, defaults to connector_radius * 1.33)
                        - "connector_collar_length" (float)
                        - "connector_num_sides" (int)
                        - "world_up" (list/Vector)
                        - "world_folder" (str)
                        - "tile_size" (int)
                        - "reference_position" (list/Vector)
                        - "reference_tile" (list/Vector)
                        - "profile_top_wire" (list of lists/Vectors)
                        - "profile_bottom_wire" (list of lists/Vectors)
                        - "mast_types" (dict)
                        - "masts" (dict)
    """
    material_name = params.get("material_name", MATERIAL_NAME)
    material_msts_texture_name = params.get("material_msts_texture_name", MATERIAL_MSTS_TEXTURE_NAME)
    lod_distance_meters = params.get("lod_distance_meters", LOD_DISTANCE_METERS)
    top_wire_span_resolution = params.get("top_wire_span_resolution", TOP_WIRE_SPAN_RESOLUTION)
    top_wire_sag_clearance = params.get("top_wire_sag_clearance", TOP_WIRE_SAG_CLEARANCE)
    top_wire_sag_height = params.get("top_wire_sag_height", TOP_WIRE_SAG_HEIGHT)
    connector_distance_meters = params.get("connector_distance_meters", CONNECTOR_DISTANCE_METERS)
    connector_radius = params.get("connector_radius", CONNECTOR_RADIUS)
    connector_collar_radius = params.get("connector_collar_radius", CONNECTOR_COLLAR_RADIUS)
    connector_collar_length = params.get("connector_collar_length", CONNECTOR_COLLAR_LENGTH)
    connector_num_sides = params.get("connector_num_sides", CONNECTOR_NUM_SIDES)
    
    world_up = params.get("world_up", WORLD_UP)
    world_folder = params.get("world_folder", WORLD_FOLDER)
    tile_size = params.get("tile_size", TILE_SIZE)
    
    reference_position = params.get("reference_position", REFERENCE_POSITION)
    reference_tile = params.get("reference_tile", REFERENCE_TILE)

    if not isinstance(world_up, Vector):
        world_up = Vector(world_up)

    if not isinstance(reference_position, Vector):
        reference_position = Vector(reference_position)

    if not isinstance(reference_tile, Vector):
        reference_tile = Vector(reference_tile)

    profile_top_wire = params.get("profile_top_wire", PROFILE_TOP_WIRE)
    profile_bottom_wire = params.get("profile_bottom_wire", PROFILE_BOTTOM_WIRE)
    
    mast_types = params.get("mast_types", MAST_TYPES)
    masts_config = params.get("masts", {})

    for name, masts in masts_config.items():
        top_mast_points, bottom_mast_points = calculate_mast_wire_positions(
            masts,
            mast_types,
            tile_size,
            reference_position,
            reference_tile,
            world_folder
        )
        
        top_wire_points = build_top_wire(
            name,
            top_mast_points,
            bottom_mast_points,
            lod_distance_meters,
            material_name,
            material_msts_texture_name,
            world_up,
            top_wire_span_resolution,
            top_wire_sag_clearance,
            top_wire_sag_height,
            profile_top_wire
        )

        bottom_wire_points = build_bottom_wire(
            name,
            top_mast_points,
            bottom_mast_points,
            lod_distance_meters,
            material_name,
            material_msts_texture_name,
            world_up,
            profile_bottom_wire
        )

        if top_wire_points is not None and bottom_wire_points is not None:
            build_connectors(
                name,
                top_wire_points,
                bottom_wire_points,
                lod_distance_meters,
                material_name,
                material_msts_texture_name,
                world_up,
                connector_distance_meters,
                connector_radius,
                connector_collar_radius,
                connector_collar_length,
                connector_num_sides
            )



