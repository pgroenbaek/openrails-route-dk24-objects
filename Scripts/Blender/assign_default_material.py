# Assign subobjects a default material and remove all other materials in Blender 4.2.

import bpy

def create_default_material():
    mat_name = "Default"
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]
    mat = bpy.data.materials.new(name=mat_name)
    return mat

def assign_material_to_objects(mat):
    for obj in bpy.data.objects:
        if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
            if obj.data.materials:
                obj.data.materials.clear()
            obj.data.materials.append(mat)

def remove_other_materials():
    materials_to_remove = [mat for mat in bpy.data.materials if mat.name != "Default"]
    for mat in materials_to_remove:
        bpy.data.materials.remove(mat)


default_mat = create_default_material()
assign_material_to_objects(default_mat)
remove_other_materials()