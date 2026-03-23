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

INPUT_FOLDER = "D:/Games/Open Rails/Content/PGA DK24/UTILS/stations"
STATION_NAME = "Tommerup"

with open(f"{INPUT_FOLDER}/{STATION_NAME}.json", "r") as f:
    data = json.load(f)

station_name = data["station_name"]
reference_x = data["reference_x"]
reference_y = data["reference_y"]
reference_z = data["reference_z"]

reference_tile_x = data["reference_tile_x"]
reference_tile_y = data["reference_tile_y"]

platforms = data["platforms"]

for platform in platforms:
    platform_name = platform["platform_name"]
    platform_coords = platform["platform_coords"]
    curve_data = bpy.data.curves.new(name=platform_name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 12
    polyline = curve_data.splines.new('POLY')
    polyline.points.add(len(platform_coords)-1)
    for i, (x, y, z) in enumerate(platform_coords):
        polyline.points[i].co = (x, y, z, 1)
    curve_obj = bpy.data.objects.new(platform_name, curve_data)
    bpy.context.collection.objects.link(curve_obj)
