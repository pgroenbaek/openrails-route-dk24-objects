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
MATERIAL_MSTS_TEXTURE_NAME = "DB_Rails1.png"
LOD_DISTANCE_METERS = 500

WIRE_NAME = "ReturnWire"
WIRE_SPAN_RESOLUTION = 6
WIRE_THICKNESS = 0.03
WIRE_SAG_RATIO = 0.011

WORLD_UP = Vector((0, 0, 1))
WORLD_FOLDER = "/media/peter/T7 Shield/Repos/personal/openrails-route-dk24/ROUTES/OR_DK24/WORLD"

TILE_SIZE = 2048

# This position and tile is where to place the generated object in world coordinates.
# Rotation of the object should be QDirection( 0 0 0 1 ).
REFERENCE_POSITION = Vector((-874.908, 14.4113, -828.282))
REFERENCE_TILE = Vector((-5656, 15119))

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
    Calculates Blender coordinates based on position, tile coordinates, tile size,
    and a reference point.

    Args:
        position (Vector): The current position in game world coordinates (x, y, z).
        tile_coords (Vector): The tile coordinates (tile_x, tile_y) for the current position.
        tile_size (int): Size of a world tile in meters.
        reference_position (Vector): Reference position in game world coordinates.
        reference_tile (Vector): Reference tile coordinates.

    Returns:
        Vector: The corresponding 3D point in Blender's coordinate system.
    """
    blender_x = (tile_coords.x - reference_tile.x) * tile_size + (position.x - reference_position.x)
    blender_y = (tile_coords.y - reference_tile.y) * tile_size + (position.z - reference_position.z)
    blender_z = position.y - reference_position.y

    return Vector((blender_x, blender_y, blender_z))


def read_mast_data(masts, world_folder):
    """
    Reads mast data from world files based on provided mast entries.

    Args:
        masts (list): A list of mast entries, where each entry is
                      [UiD, TileX, TileY, offset_index].
        world_folder (str): Path to the Open Rails WORLD folder.

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

                    if uid is not None and uid in tiles_to_uids[(tile_x, tile_y)]:
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


def calculate_mast_wire_positions(masts, mast_types, tile_size, reference_position, reference_tile, world_folder):
    """
    Calculates the 3D attachment points for wires on masts.

    Args:
        masts (list): A list of mast entries, where each entry is
                      [UiD, TileX, TileY, offset_index].
        mast_types (dict): Dictionary defining mast types and their attachment offsets.
        tile_size (int): Size of a world tile in meters.
        reference_position (Vector): Reference position in game world coordinates.
        reference_tile (Vector): Reference tile coordinates.
        world_folder (str): Path to the Open Rails WORLD folder.

    Returns:
        list: A list of Vector objects representing wire attachment points.
    """
    wire_mast_points = []
    mast_data = read_mast_data(masts, world_folder)

    for mast_entry in mast_data:
        mast_tile = Vector((mast_entry[1], mast_entry[2]))
        mast_position = calculate_blender_coordinates(mast_entry[4], mast_tile, tile_size, reference_position, reference_tile)
        mast_rotation = mast_entry[5]
        mast_type_key = mast_entry[3]
        offset_index = mast_entry[6]

        if mast_type_key not in mast_types:
            print(f"Warning: Mast type '{mast_type_key}' from entry not defined in MAST_TYPES. Skipping mast.")
            continue

        if offset_index >= len(mast_types[mast_type_key]):
            print(f"Warning: Invalid offset index '{offset_index}' for type '{mast_type_key}'. Skipping mast.")
            continue

        mast_definition = mast_types[mast_type_key][offset_index]
        mast_forward = mast_rotation @ Vector((1, 0, 0))
        mast_right = mast_rotation @ Vector((0, 1, 0))
        mast_up = mast_rotation @ Vector((0, 0, 1))

        attachment_point_local = Vector((
            mast_definition["offset"].y,
            mast_definition["offset"].x,
            mast_definition["offset"].z
        ))

        attachment_point = mast_position + (
            mast_right * attachment_point_local.x +
            mast_forward * attachment_point_local.y +
            mast_up * attachment_point_local.z
        )

        wire_mast_points.append(attachment_point)

    return wire_mast_points


def build_wire(name, wire_attachment_points, wire_name, wire_span_resolution, wire_sag_ratio, world_up, profile_wire, lod_distance, material_name, material_msts_texture_name):
    """
    Generates a 3D wire mesh in Blender based on a series of attachment points.

    Args:
        name (str): Base name for the Blender object and mesh.
        wire_attachment_points (list): List of Vector objects defining the wire attachment points.
        wire_name (str): Name suffix for the generated wire object.
        wire_span_resolution (int): Number of subdivisions used for each wire span.
        wire_sag_ratio (float): Sag amount as a ratio of each span length.
        world_up (Vector): World up direction used when generating the wire geometry.
        profile_wire (list): 2D wire profile containing profile offsets and texture coordinates.
        lod_distance (float): LOD distance in meters.
        material_name (str): Name of the material to assign to the wire.
        material_msts_texture_name (str): MSTS/ORTS texture name for the material.

    Returns:
        bpy.types.Object or None: The generated Blender object, or None if no path points were generated.
    """
    wire_path_points = []

    for segment_index in range(len(wire_attachment_points) - 1):
        start_point = wire_attachment_points[segment_index]
        end_point = wire_attachment_points[segment_index + 1]
        span_length = (end_point - start_point).length
        max_sag_for_this_span = span_length * wire_sag_ratio

        for span_sub_index in range(wire_span_resolution + 1):
            interpolation_factor = span_sub_index / wire_span_resolution
            interpolated_base_point = start_point.lerp(end_point, interpolation_factor)
            arch_factor = 4 * interpolation_factor * (1 - interpolation_factor)
            sag_amount = max_sag_for_this_span * arch_factor
            wire_point = interpolated_base_point - world_up * sag_amount
            wire_path_points.append(wire_point)

    if not wire_path_points:
        print("Warning: No path points generated for wire. Skipping mesh creation.")
        return None

    mesh_vertices = []
    mesh_uvs = []
    mesh_faces = []
    profile_point_count = len(profile_wire)

    for i in range(len(wire_path_points)):
        current_path_point = wire_path_points[i]

        if i < len(wire_path_points) - 1:
            segment_direction = wire_path_points[i + 1] - current_path_point
        elif i > 0:
            segment_direction = current_path_point - wire_path_points[i - 1]
        else:
            segment_direction = Vector((1, 0, 0))

        if segment_direction.length_squared < 1e-6:
            segment_direction = Vector((1, 0, 0))
        else:
            segment_direction.normalize()

        right_vector = segment_direction.cross(world_up)

        if right_vector.length_squared < 1e-12:
            right_vector = Vector((1, 0, 0)).cross(segment_direction)

        right_vector.normalize()
        upward_vector = right_vector.cross(segment_direction).normalized()
        base_vertex_index = len(mesh_vertices)

        for profile_offset, texcoord in profile_wire:
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

    mesh = bpy.data.meshes.new(f"{name}_{wire_name}")
    obj = bpy.data.objects.new(f"{name}_{wire_name}", mesh)

    link_object_to_lod_collection(obj, lod_distance)

    material = assign_material(obj, material_name)
    material_index = obj.data.materials.find(material.name)

    set_exporter_texture_name(material, material_msts_texture_name)

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


def perform_operation(params):
    """
    Blender operation to generate return wires between configured mast attachment points.

    Args:
        params (dict): A dictionary containing configuration parameters for the operation.
                       Expected keys include:
                       - "material_name" (str)
                       - "material_msts_texture_name" (str)
                       - "lod_distance_meters" (float)
                       - "wire_name" (str)
                       - "wire_span_resolution" (int)
                       - "wire_thickness" (float)
                       - "wire_sag_ratio" (float)
                       - "world_up" (list/Vector)
                       - "world_folder" (str)
                       - "tile_size" (int)
                       - "reference_position" (list/Vector)
                       - "reference_tile" (list/Vector)
                       - "profile_wire" (list)
                       - "mast_types" (dict)
                       - "masts" (dict)
    """
    material_name = params.get("material_name", MATERIAL_NAME)
    material_msts_texture_name = params.get("material_msts_texture_name", MATERIAL_MSTS_TEXTURE_NAME)
    lod_distance = params.get("lod_distance_meters", LOD_DISTANCE_METERS)
    wire_name = params.get("wire_name", WIRE_NAME)
    wire_span_resolution = params.get("wire_span_resolution", WIRE_SPAN_RESOLUTION)
    wire_thickness = params.get("wire_thickness", WIRE_THICKNESS)
    wire_sag_ratio = params.get("wire_sag_ratio", WIRE_SAG_RATIO)

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

    profile_wire = params.get("profile_wire", PROFILE_WIRE)

    mast_types = params.get("mast_types", MAST_TYPES)
    masts_config = params.get("masts", {})

    for name, masts in masts_config.items():
        wire_attachment_points = calculate_mast_wire_positions(
            masts,
            mast_types,
            tile_size,
            reference_position,
            reference_tile,
            world_folder
        )

        build_wire(
            name,
            wire_attachment_points,
            wire_name,
            wire_span_resolution,
            wire_sag_ratio,
            world_up,
            profile_wire,
            lod_distance,
            material_name,
            material_msts_texture_name
        )