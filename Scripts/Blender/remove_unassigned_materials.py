# Removes all materials that are not assigned to a subobject in Blender 4.2.

import bpy

def remove_unassigned_materials():
    assigned_materials = {mat for obj in bpy.data.objects if obj.data and hasattr(obj.data, 'materials') for mat in obj.data.materials if mat}
    for mat in list(bpy.data.materials):
        if mat not in assigned_materials:
            bpy.data.materials.remove(mat)


remove_unassigned_materials()