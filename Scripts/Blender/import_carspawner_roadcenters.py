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
import json
from mathutils import Vector


INPUT_FOLDER = "D:/Games/Open Rails/Content/PGA DK24/DATA/roadcenters"
ROADCENTER_INPUT_NAME = "Test"


def create_carspawner_curves(data):
    """
    Creates Blender curve objects for each carspawner defined in the roadcenter JSON.

    Reads carspawner coordinate data and generates a POLY spline curve for
    each carspawner, preserving the exact vertex positions.

    Args:
        data (dict): Parsed JSON data containing roadcenter and carspawner information.

    Notes:
        - Each carspawner becomes a separate Curve object.
        - Curves are created using POLY splines to preserve straight segments.
        - Objects are linked to the active Blender collection.
    """
    reference_x = data["reference_x"]
    reference_y = data["reference_y"]
    reference_z = data["reference_z"]
    reference_tile_x = data["reference_tile_x"]
    reference_tile_y = data["reference_tile_y"]
    carspawners = data["carspawners"]
    for carspawner in carspawners:
        carspawner_name = carspawner["carspawner_name"]
        carspawner_coords = carspawner["carspawner_coords"]
        curve_data = bpy.data.curves.new(name=carspawner_name, type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.resolution_u = 12
        polyline = curve_data.splines.new('POLY')
        polyline.points.add(len(carspawner_coords)-1)
        for i, (x, y, z) in enumerate(carspawner_coords):
            polyline.points[i].co = (x, y, z, 1)
        curve_obj = bpy.data.objects.new(carspawner_name, curve_data)
        bpy.context.collection.objects.link(curve_obj)


def load_roadcenter_json(input_folder, roadcenter_name):
    """
    Loads carspawner roadcenter data from a JSON file.

    Args:
        input_folder (str): Directory containing roadcenter JSON files.
        roadcenter_name (str): Name of the roadcenter JSON file (without extension).

    Returns:
        dict: Parsed JSON data for the carspawner roadcenters.
    """
    with open(f"{input_folder}/{roadcenter_name}.json", "r") as f:
        data = json.load(f)
    return data


data = load_roadcenter_json(INPUT_FOLDER, ROADCENTER_INPUT_NAME)
create_carspawner_curves(data)