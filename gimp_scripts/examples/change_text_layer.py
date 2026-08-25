#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This is a GIMP Python-fu script. It is NOT intended to be run directly by Blender.
# Instead, Blender's process_image_gimp.py will call GIMP, and GIMP will execute this script
# in batch mode to perform the desired image manipulation.

# To make this script available to GIMP in batch mode, you need to register it using
# gimpfu.register. The function name in gimpfu.register must match the
# '(python-fu-FUNCTION_NAME ...)' call from process_image_gimp.py.

from gimpfu import *

def python_fu_change_text_layer(image, drawable, input_path, output_path, text_layer_name, new_text):
    """
    Changes the text of a specified text layer in an XCF file and saves it.

    Args:
        image (gimp.Image): The current GIMP image object (automatically passed).
        drawable (gimp.Drawable): The current drawable (automatically passed).
        input_path (str): The full path to the input image file (XCF).
        output_path (str): The full path where the modified image should be saved.
        text_layer_name (str): The name of the text layer to modify.
        new_text (str): The new text to set for the layer.
    """
    # Open the image explicitly if not already loaded (useful for batch mode)
    # GIMP batch mode usually loads the image passed as an argument, but
    # for robust script-fu usage with direct paths, this is safer.
    # If the image is already opened, this might create a duplicate in GIMP's memory.
    # For a simple text change, we assume 'image' is the one passed from the command line.

    # Find the text layer by name
    text_layer = None
    for layer in image.layers:
        if layer.name == text_layer_name and pdb.gimp_item_is_text_layer(layer):
            text_layer = layer
            break

    if text_layer:
        # Change the text
        pdb.gimp_text_layer_set_text(text_layer, new_text)
        print(f"Text layer '{text_layer_name}' updated to: '{new_text}'")
    else:
        print(f"Warning: Text layer '{text_layer_name}' not found. Cannot change text.")

    # Save the modified image
    # Note: Using gimp_xcf_save for .xcf files to preserve layers
    # For other formats like PNG, use pdb.gimp_file_save with correct args.
    try:
        # Ensure path exists for output
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # GIMP 2.10+ uses gimp_file_save
        pdb.gimp_file_save(image, drawable, output_path, output_path)
        print(f"Image saved to: {output_path}")
    except Exception as e:
        print(f"Error saving image: {e}", file=sys.stderr)
        # Attempt a more generic save if specific XCF save fails or is deprecated
        try:
            # Fallback for older GIMP versions or different file types
            # pdb.gimp_xcf_save is for XCF
            # pdb.gimp_png_save is for PNG
            # It's better to use pdb.gimp_file_save
            pass
        except Exception as fallback_e:
            print(f"Fallback save also failed: {fallback_e}", file=sys.stderr)


# Register the script with GIMP
register(
    "python_fu_change_text_layer",  # Name used in GIMP's PDB and by external calls
    "Change Text Layer in Image",
    "Changes the text content of a specified text layer in an XCF image.",
    "Your Name",
    "Your Name",
    "2026",
    "<Image>/Python-Fu/MyScripts/Change Text Layer...", # Menu path (optional for batch scripts)
    "*", # Applicable image types (any image)
    [
        (PF_STRING, "input_path", "Input Image Path", ""),
        (PF_STRING, "output_path", "Output Image Path", ""),
        (PF_STRING, "text_layer_name", "Text Layer Name", ""),
        (PF_STRING, "new_text", "New Text", "")
    ],
    [],
    python_fu_change_text_layer,
    menu="/Python-Fu/MyScripts" # This ensures it appears in the menu for testing, but not strictly needed for batch
)

# Call the main function if running as a script within GIMP
main()
