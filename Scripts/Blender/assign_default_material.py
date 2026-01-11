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


def create_default_material():
    """
    Creates or retrieves a default material named 'Default'.

    Returns:
        bpy.types.Material: The 'Default' material.
    """
    mat_name = "Default"
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]
    mat = bpy.data.materials.new(name=mat_name)
    return mat


def assign_material_to_objects(mat):
    """
    Assigns a given material to all applicable objects in the Blender scene.

    Args:
        mat (bpy.types.Material): The material to assign.
    """
    for obj in bpy.data.objects:
        if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
            if obj.data.materials:
                obj.data.materials.clear()
            obj.data.materials.append(mat)


def remove_other_materials():
    """
    Removes all materials from the Blender project except for the 'Default' material.

    Warnings:
        - Use with caution, as this operation is destructive and PERMANENTLY REMOVES ALL MATERIALS from the project that are not named "Default".
    """
    materials_to_remove = [mat for mat in bpy.data.materials if mat.name != "Default"]
    for mat in materials_to_remove:
        bpy.data.materials.remove(mat)


default_mat = create_default_material()
assign_material_to_objects(default_mat)
remove_other_materials()