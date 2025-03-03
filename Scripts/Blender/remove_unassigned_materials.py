import bpy

def remove_unassigned_materials():
    """
    Remove all unassigned materials from the Blender project.

    This function iterates through all objects in the Blender scene and collects 
    materials that are actively assigned to object data. It then removes any materials 
    from `bpy.data.materials` that are not assigned to any object.

    Warnings:
        - This operation is destructive and WILL PERMANENTLY DELETE UNASSIGNED MATERIALS.
        - Ensure that any materials you want to keep are assigned to at least one object.
    """
    assigned_materials = {mat for obj in bpy.data.objects if obj.data and hasattr(obj.data, 'materials') for mat in obj.data.materials if mat}
    for mat in list(bpy.data.materials):
        if mat not in assigned_materials:
            bpy.data.materials.remove(mat)


remove_unassigned_materials()