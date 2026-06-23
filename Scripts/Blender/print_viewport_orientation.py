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


def print_viewport_orientation():
    """
    Prints the viewport orientation (what you are actually looking through)
    as Euler angles in radians.
    """
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            region_3d = area.spaces.active.region_3d
            rotation = region_3d.view_rotation.to_euler()
            print("Rotation (radians):")
            print("X (pitch):", rotation.x)
            print("Y (roll): ", rotation.y)
            print("Z (yaw):  ", rotation.z)
            return rotation
    print("Run this in a screen with a 3D Viewport.")
    return None


print_viewport_orientation()


