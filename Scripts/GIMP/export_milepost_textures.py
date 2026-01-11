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

import os
import copy
import subprocess
from gimpfu import *


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
    return filter(lambda x: x.name == textlayer_name, image.layers)[0]


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




from_km = 0
to_km = 249
image_name = "PGA_DKMilepost_x_y.xcf"
textlayer_name_km = "KM"
textlayer_name_m = "M"
export_path = "D:/Games/Open Rails/Modelling/DK24/DKMilepost/TextureExport"
aceit_path = "D:/Games/Open Rails/Tools/AceIt/aceit.exe"

ensure_directory_exists(export_path)

image = find_image(image_name)
textlayer_km = find_textlayer(image, textlayer_name_km)
textlayer_m = find_textlayer(image, textlayer_name_m)

for km in range(from_km, to_km + 1):
    for m in [0, 2, 4, 6, 8]:
        texture_name = "PGA_DKSign_Location_%03d_%d" % (km, m)
        png_filepath = "%s/%s.png" % (export_path, texture_name)
        text_km = str(km)
        text_m = str(m)
        set_textlayer_text(textlayer_km, text_km, font="NimbusSanL Bold", font_size=110, color=gimpcolor.RGB(0,0,0))
        set_textlayer_text(textlayer_m, text_m, font="NimbusSanL Bold", font_size=73, color=gimpcolor.RGB(0,0,0))
        ensure_file_exists(png_filepath)
        export_png(image, png_filepath)
        subprocess.call([aceit_path, png_filepath, "-q"])
        os.remove(png_filepath)
