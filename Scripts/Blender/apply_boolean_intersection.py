# Apply a boolean intersection to selected objects in Blender 4.2.

import bpy

def apply_boolean_intersection():
    """
    Applies a Boolean intersection operation to selected mesh objects in Blender.

    This function:
    - Ensures at least two objects are selected.
    - Fixes normals for all selected mesh objects before applying the Boolean operation.
    - Applies Boolean intersection modifiers sequentially to keep only shared volume.
    - Deletes all objects except the primary one after merging.

    Notes:
        - Only works on mesh objects.
        - The first selected object acts as the base object for the intersection.
        - The Boolean modifier is applied, and the extra objects are deleted.

    Warnings:
        - This operation is destructive; removed objects cannot be recovered.
        - Ensure you have a backup before running.

    """
    selected_objects = bpy.context.selected_objects
    if len(selected_objects) < 2:
        print("Please select at least two objects for the intersection.")
    else:
        for obj in selected_objects:
            if obj.type == 'MESH':
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.normals_make_consistent(inside=False)
                bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        main_object = selected_objects[0]
        main_object.select_set(True)
        bpy.context.view_layer.objects.active = main_object
        for obj in selected_objects[1:]:
            bool_mod = main_object.modifiers.new(name="Boolean", type='BOOLEAN')
            bool_mod.operation = 'INTERSECT'
            bool_mod.use_self = False
            bool_mod.object = obj
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        for obj in selected_objects[1:]:
            bpy.data.objects.remove(obj)
        print("Boolean intersection completed successfully with fixed normals.")


apply_boolean_intersection()
