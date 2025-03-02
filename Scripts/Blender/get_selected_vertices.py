import bpy

def get_selected_vertices():
    """
    Retrieves the coordinates of all selected vertices in the active mesh object.

    This function temporarily switches the object to 'OBJECT' mode to access vertex selection data, 
    collects the coordinates of all selected vertices, prints them, and then restores the original mode.

    Returns:
        None
    """
    mode = bpy.context.active_object.mode
    bpy.ops.object.mode_set(mode='OBJECT')
    selected_verts = [v.co for v in bpy.context.active_object.data.vertices if v.select]
    print(selected_verts)
    bpy.ops.object.mode_set(mode=mode)

get_selected_vertices()