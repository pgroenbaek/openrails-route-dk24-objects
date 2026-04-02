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
import bmesh


MATERIAL_NAME = "Embankment"


def assign_material_to_selection(material_name):
    """
    Assign a material to all currently selected faces of the active mesh.

    Ensures the material exists and is added to the object's material slots
    before assigning it to the selected faces.

    Args:
        material_name (str): Name of the material to assign.
    """
    obj = bpy.context.object
    mesh = obj.data
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(mesh)
    material = bpy.data.materials.get(material_name)
    if material is None:
        material = bpy.data.materials.new(name=material_name)
    if material.name not in [m.name for m in obj.data.materials]:
        obj.data.materials.append(material)
    material_index = obj.data.materials.find(material.name)
    for face in bm.faces:
        if face.select:
            face.material_index = material_index
    bmesh.update_edit_mesh(mesh)


assign_material_to_selection(MATERIAL_NAME)