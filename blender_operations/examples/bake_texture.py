import bpy
import os
import sys
import mathutils

# Get the directory of the current script
_script_dir = os.path.dirname(os.path.abspath(__file__))
_baked_textures_dir = os.path.join(_script_dir, "baked_textures")

def ensure_directory_exists(path):
    """Ensures that the given directory path exists, creating it if necessary."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def blender_bake_texture_operation(params):
    """
    Triggers a bake operation in Blender for a specified object and saves the result.

    Parameters:
        params (dict): A dictionary containing:
            'name' (str): Name of the operation.
            'object_name' (str): The name of the object to bake.
            'bake_type' (str): The type of bake (e.g., 'COMBINED', 'NORMAL', 'AO', 'DIFFUSE').
                                See bpy.types.BakeSettings.use_pass_... for full list.
            'image_name' (str): Name for the new image datablock in Blender.
            'image_width' (int): Width of the baked image.
            'image_height' (int): Height of the baked image.
            'image_path' (str): Relative path within the script directory where the image will be saved.
            'uv_map' (str, optional): Name of the UV map to use. Defaults to active UV map if not provided.
            'margin' (int, optional): The bake margin in pixels. Defaults to 16.
            'clear' (bool, optional): Clear the image before baking. Defaults to True.
            'save_as_file' (bool, optional): Whether to save the baked image to a file. Defaults to True.
            'filepath' (str, optional): The file path relative to the script's directory to save the image.
                                        If 'save_as_file' is True, this is required.
    """
    print(f"Starting bake operation: {params['name']}")

    object_name = params['object_name']
    bake_type = params['bake_type']
    image_name = params['image_name']
    image_width = params['image_width']
    image_height = params['image_height']
    image_path_relative = params['image_path']
    uv_map_name = params.get('uv_map')
    margin = params.get('margin', 16)
    clear = params.get('clear', True)
    save_as_file = params.get('save_as_file', True)
    output_filepath_relative = params.get('filepath')

    # Ensure output directory exists for baked textures
    if save_as_file:
        ensure_directory_exists(_baked_textures_dir)
        output_filepath = os.path.join(_script_dir, output_filepath_relative)
    else:
        output_filepath = None

    obj = bpy.data.objects.get(object_name)
    if not obj:
        print(f"Error: Object '{object_name}' not found for baking.", file=sys.stderr)
        return

    # Select the object and make it active
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Ensure the object has an active UV map
    if not obj.data.uv_layers:
        print(f"Error: Object '{object_name}' has no UV maps. Cannot bake.", file=sys.stderr)
        return

    if uv_map_name:
        if uv_map_name not in obj.data.uv_layers:
            print(f"Warning: UV map '{uv_map_name}' not found on object '{object_name}'. Using active UV map.", file=sys.stderr)
        else:
            obj.data.uv_layers[uv_map_name].active = True
            print(f"Set UV map '{uv_map_name}' as active for object '{object_name}'.")

    # Create a new image or get an existing one
    baked_image = bpy.data.images.get(image_name)
    if not baked_image:
        baked_image = bpy.data.images.new(name=image_name, width=image_width, height=image_height)
        print(f"Created new image '{image_name}' ({image_width}x{image_height}).")
    else:
        # Resize if necessary
        if baked_image.size[0] != image_width or baked_image.size[1] != image_height:
            baked_image.scale(image_width, image_height)
            print(f"Resized existing image '{image_name}' to ({image_width}x{image_height}).")
        print(f"Using existing image '{image_name}'.")


    # Assign the image to a new material or an existing material's image texture node
    # This is crucial for the bake target. The active image texture node in an active material
    # will be the target for the bake.

    # Check if the object has materials, if not, create a simple one
    if not obj.data.materials:
        mat = bpy.data.materials.new(name=f"{object_name}_BakeMaterial")
        obj.data.materials.append(mat)
        print(f"Created new material '{mat.name}' for object '{object_name}'.")
    else:
        mat = obj.data.materials[0] # Use the first material

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Ensure a principled BSDF is present (common default)
    principled_node = nodes.get("Principled BSDF")
    if not principled_node:
        principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
        principled_node.location = 0, 0
        output_node = nodes.get("Material Output")
        if output_node:
            links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])

    # Create or get an Image Texture node and link the baked_image to it
    bake_image_node = nodes.get(f"{image_name}_Node")
    if not bake_image_node:
        bake_image_node = nodes.new(type='ShaderNodeTexImage')
        bake_image_node.name = f"{image_name}_Node"
        bake_image_node.location = -300, 300 # Position it to the left
        if principled_node: # Try to place it near principled
             bake_image_node.location = principled_node.location[0] - 300, principled_node.location[1] + 300
        print(f"Created new Image Texture node '{bake_image_node.name}'.")

    bake_image_node.image = baked_image
    # Make sure this node is selected for the bake operation
    bake_image_node.select = True
    nodes.active = bake_image_node
    print(f"Set image '{baked_image.name}' to node '{bake_image_node.name}' and made node active.")

    # Set bake settings
    bpy.context.scene.render.engine = 'CYCLES' # Cycles is required for baking
    bpy.context.scene.cycles.bake_type = bake_type
    bpy.context.scene.render.bake.use_clear = clear
    bpy.context.scene.render.bake.margin = margin
    bpy.context.scene.render.bake.cage_extrusion = 0.0 # Default to 0, adjust if needed for complex meshes
    bpy.context.scene.render.bake.max_ray_distance = 0.0 # Default to 0

    # For diffuse bake, control what's included
    if bake_type == 'DIFFUSE':
        bpy.context.scene.render.bake.diffuse_direct = params.get('diffuse_direct', True)
        bpy.context.scene.render.bake.diffuse_indirect = params.get('diffuse_indirect', False)
        bpy.context.scene.render.bake.diffuse_color = params.get('diffuse_color', True)
        print(f"Diffuse bake settings: direct={bpy.context.scene.render.bake.diffuse_direct}, "
              f"indirect={bpy.context.scene.render.bake.diffuse_indirect}, "
              f"color={bpy.context.scene.render.bake.diffuse_color}")


    print(f"Baking '{bake_type}' for object '{object_name}'...")
    try:
        bpy.ops.object.bake(type=bake_type)
        print("Bake completed successfully.")

        if save_as_file and output_filepath:
            print(f"Saving baked image to: {output_filepath}")
            # Blender requires full path for saving, and it prefers forward slashes
            baked_image.filepath_raw = bpy.path.abspath(output_filepath)
            baked_image.file_format = 'PNG' # Or other format like 'OPEN_EXR', 'JPEG'
            baked_image.save()
            print(f"Image '{image_name}' saved to '{output_filepath}'.")
        else:
            print("Baked image not saved to file (save_as_file is False or no filepath provided).")

    except Exception as e:
        print(f"An error occurred during baking: {e}", file=sys.stderr)

    # Clean up selection
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = None
    print(f"Operation '{params['name']}' completed.")
