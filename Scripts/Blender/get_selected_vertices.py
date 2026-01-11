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

def get_selected_vertices():
    """
    Retrieves the coordinates of all selected vertices in the active mesh object.

    This function temporarily switches the object to 'OBJECT' mode to access vertex selection data, 
    collects the coordinates of all selected vertices, prints them, and then restores the original mode.
    """
    mode = bpy.context.active_object.mode
    bpy.ops.object.mode_set(mode='OBJECT')
    selected_verts = [v.co for v in bpy.context.active_object.data.vertices if v.select]
    print(selected_verts)
    bpy.ops.object.mode_set(mode=mode)


get_selected_vertices()