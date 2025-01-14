# Exports DK24 milepost textures as .png from GIMP 2.0 and converts them to .ace via AceIt.

import os
import copy
import subprocess
from gimpfu import *

def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def ensure_file_exists(path):
    with open(path, 'w') as f:
        pass

def find_image(image_name):
    return filter(lambda x: x.name == image_name, gimp.image_list())[0]

def find_textlayer(image, textlayer_name):
    return filter(lambda x: x.name == textlayer_name_n, image.layers)[0]

def set_textlayer_text(textlayer, text, font="NimbusSanL Bold", font_size=48, letter_spacing=0, color=gimpcolor.RGB(0,0,0)):
    pdb.gimp_text_layer_set_text(textlayer, text)
    pdb.gimp_text_layer_set_font(textlayer, font)
    pdb.gimp_text_layer_set_color(textlayer, color)
    pdb.gimp_text_layer_set_font_size(textlayer, font_size, 0)
    pdb.gimp_text_layer_set_letter_spacing(textlayer, letter_spacing)

def export_png(image, filepath):
    export_image = pdb.gimp_image_duplicate(image)
    export_layer = pdb.gimp_image_merge_visible_layers(export_image, CLIP_TO_IMAGE)
    pdb.gimp_file_save(export_image, export_layer, filepath, '?')
    pdb.gimp_image_delete(export_image)


from_km = 0
to_km = 249
image_name = "PGA_DKMilepost_x_y.xcf"
textlayer_name_km = "KM"
textlayer_name_m = "M"
export_path = "D:\\Games\\Open Rails\\Modelling\\DK24\\DKMilepost\\TextureExport"
aceit_path = "D:\\Games\\Open Rails\\Tools\\AceIt\\aceit.exe"

ensure_directory_exists(export_path)

image = find_image(image_name)
textlayer_km = find_textlayer(image, textlayer_name_km)
textlayer_m = find_textlayer(image, textlayer_name_m)

for km in range(from_km, to_km + 1):
    for m in [0, 2, 4, 6, 8]:
        texture_name = "PGA_DKMilepost_%03d_%d" % (km, m)
        png_filepath = "%s\\%s.png" % (export_path, texture_name)
        ace_filepath = "%s\\%s.ace" % (export_path, texture_name)

        text_km = "%s" % (km)
        text_m = "%s" % (m)
        set_textlayer_text(textlayer_km, text_km, font="NimbusSanL Bold", font_size=110, color=gimpcolor.RGB(0,0,0))
        set_textlayer_text(textlayer_m, text_m, font="NimbusSanL Bold", font_size=73, color=gimpcolor.RGB(0,0,0))

        ensure_file_exists(png_filepath)

        export_png(image, png_filepath)
        subprocess.call([aceit_path, png_filepath, ace_filepath, "-q"])
        os.remove(png_filepath)
