# Exports DK24 ETCSL2 numbersign textures as .png from GIMP 2.0 and converts them to .ace via AceIt.

import os
import copy
import subprocess
from gimpfu import *


def to_filename(signnumber):
    """
    Converts a given sign number into a valid filename by removing hyphens.

    Args:
        signnumber (str): The string (sign number) to be converted.

    Returns:
        str: A filename-safe version of the input string with hyphens removed.
    """
    name = copy.deepcopy(signnumber)
    name = name.replace("-", "")
    return name


def ensure_directory_exists(path):
    """
    Ensures that a directory exists at the given path. If the directory does not exist, it is created.

    Args:
        path (str): The directory path to check and create if necessary.
    """
    if not os.path.exists(path):
        os.makedirs(path)


def ensure_file_exists(path):
    """
    Ensures that a file exists at the specified path. If the file does not exist, it is created.

    Args:
        path (str): The file path to check and create if necessary.
    """
    with open(path, 'w') as f:
        pass


def find_image(image_name):
    """
    Finds an image in GIMP by its name.

    Args:
        image_name (str): The name of the image to search for.

    Returns:
        gimp.Image: The first image found with the specified name.

    Raises:
        IndexError: If no image with the specified name is found.
    """
    return filter(lambda x: x.name == image_name, gimp.image_list())[0]


def find_textlayer(image, textlayer_name):
    """
    Finds a text layer by its name within a given image in GIMP.

    Args:
        image (gimp.Image): The image in which to search for the text layer.
        textlayer_name (str): The name of the text layer to search for.

    Returns:
        gimp.Layer: The first text layer found with the specified name.

    Raises:
        IndexError: If no text layer with the specified name is found.
    """
    return filter(lambda x: x.name == textlayer_name_n, image.layers)[0]


def set_textlayer_text(textlayer, text, font="NimbusSanL Bold", font_size=48, letter_spacing=0, color=gimpcolor.RGB(0,0,0)):
    """
    Sets the text and styling for a text layer in GIMP.

    Args:
        textlayer (gimp.Layer): The text layer to modify.
        text (str): The text to set for the layer.
        font (str, optional): The font to use for the text. Default is "NimbusSanL Bold".
        font_size (int, optional): The font size for the text. Default is 48.
        letter_spacing (int, optional): The letter spacing for the text. Default is 0.
        color (gimpcolor.RGB, optional): The color of the text. Default is black (RGB(0, 0, 0)).
    """
    pdb.gimp_text_layer_set_text(textlayer, text)
    pdb.gimp_text_layer_set_font(textlayer, font)
    pdb.gimp_text_layer_set_color(textlayer, color)
    pdb.gimp_text_layer_set_font_size(textlayer, font_size, 0)
    pdb.gimp_text_layer_set_letter_spacing(textlayer, letter_spacing)


def export_png(image, filepath):
    """
    Exports a GIMP image as a PNG file to the specified path.

    Args:
        image (gimp.Image): The image to export.
        filepath (str): The path where the exported PNG file will be saved.
    
    Note:
        - The exported image will be a temporary duplicate of the original, and only visible layers will be merged.
        - After export, the duplicate image is deleted.
    """
    export_image = pdb.gimp_image_duplicate(image)
    export_layer = pdb.gimp_image_merge_visible_layers(export_image, CLIP_TO_IMAGE)
    pdb.gimp_file_save(export_image, export_layer, filepath, '?')
    pdb.gimp_image_delete(export_image)



marker_numbers = [x for xs in [
    ["Ig-%03d" % (x) for x in range(56, 62 + 1)],
    ["Avh-%03d" % (x) for x in range(1, 60 + 1)],
    ["Kib-%03d" % (x) for x in range(1, 64 + 1)],
    ["Jsf-%03d" % (x) for x in range(1, 40 + 1)],
    ["Kjn-%03d" % (x) for x in range(1, 70 + 1)],
    ["Lel-%03d" % (x) for x in range(1, 60 + 1)],
    ["Bjs-%03d" % (x) for x in range(1, 60 + 1)],
    ["Ada-%03d" % (x) for x in range(1, 40 + 1)],
    ["Rg-%03d" % (x) for x in range(110, 120 + 1)],
    ["Elm-%03d" % (x) for x in range(30, 40 + 1)],
    ["Rvb-%03d" % (x) for x in range(1, 60 + 1)],
    ["Spb-%03d" % (x) for x in range(1, 60 + 1)],
    ["Kel-%03d" % (x) for x in range(1, 60 + 1)],
    ["Anb-%03d" % (x) for x in range(1, 60 + 1)],
    ["Grm-%03d" % (x) for x in range(1, 60 + 1)],
    ["Sdh-%03d" % (x) for x in range(1, 60 + 1)],
    ["Ind-%03d" % (x) for x in range(1, 60 + 1)],
    ["Nra-%03d" % (x) for x in range(1, 60 + 1)],
    ["Ka-%03d" % (x) for x in range(40, 50 + 1)]
] for x in xs]

image_name = "PGA_DKSign_ETCSL2Number_x.xcf"
textlayer_name_n = "N"
export_path = "D:\\Games\\Open Rails\\Modelling\\DK24\\Models\\DKSign\\ETCSL2\\TextureExport"
aceit_path = "D:\\Games\\Open Rails\\Tools\\AceIt\\aceit.exe"

ensure_directory_exists(export_path)

image = find_image(image_name)
textlayer_n = find_textlayer(image, textlayer_name_n)

for n in marker_numbers:
    texture_name = "PGA_DKSign_ETCSL2Number_%s" % (to_filename(n))
    png_filepath = "%s\\%s.png" % (export_path, texture_name)
    ace_filepath = "%s\\%s.ace" % (export_path, texture_name)

    set_textlayer_text(textlayer_n, n, font="NimbusSanL Bold", font_size=120, letter_spacing=-4.0, color=gimpcolor.RGB(0,0,0))

    ensure_file_exists(png_filepath)

    export_png(image, png_filepath)
    subprocess.call([aceit_path, png_filepath, ace_filepath, "-q"])
    os.remove(png_filepath)