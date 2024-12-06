# Exports DK24 location sign textures as .png from GIMP 2.0 and converts them to .ace via AceIt.

import os
import copy
import subprocess
from gimpfu import *

def to_filename(signnumber):
    path_name = copy.deepcopy(signnumber)
    path_name = copy.deepcopy(location)
    path_name = path_name.replace("Æ", "Ae")
    path_name = path_name.replace("æ", "ae")
    path_name = path_name.replace("Ø", "Oe")
    path_name = path_name.replace("ø", "oe")
    path_name = path_name.replace("Å", "Aa")
    path_name = path_name.replace("å", "aa")
    path_name = path_name.replace(" ", "")
    path_name = path_name.replace(".", "")
    return path_name

def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def ensure_file_exists(path):
    with open(path, 'w') as f:
        pass

def find_image(image, textlayer_name):
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



locations = ["Aarup", "Borup", "Ejby", "Elmelund", "Fjenneslev", "Forlev",
    "Fredericia", "Glostrup", "Helgoland", "Hellerup", "Hjulby", "Høje Taastrup",
    "Holmstrup", "Hvidovre", "Kalvebod", "Kastrup", "Kavslunde", "Klampenborg",
    "København H", "København G", "Korsør", "Marslev", "Middelfart", "Nyborg",
    "Odense", "Østerport", "Ringsted", "Roskilde", "Slagelse", "Snoghøj", "Sorø",
    "Sprogø", "Taulov", "Tommerup", "Ullerslev", "Valby", "Viby Sj.", "Vigerslev"]
image_name = "PGA_DKSign_Location_x.xcf"
textlayer_name_l = "L"
export_path = "D:\\Games\\Open Rails\\Modelling\\DK24\\Models\\DKSign\\ETCSL2\\TextureExport"
aceit_path = "D:\\Games\\Open Rails\\Tools\\AceIt\\aceit.exe"

ensure_directory_exists(export_path)

image = find_image(image_name)
textlayer_l = find_textlayer(image, textlayer_name_l)

for n in marker_numbers:
    texture_name = "PGA_DKSign_Location_%s" % (to_filename(location))
    png_filepath = "%s\\%s.png" % (export_path, texture_name)
    ace_filepath = "%s\\%s.ace" % (export_path, texture_name)

    set_textlayer_text(textlayer_l, location, font="NimbusSanL Bold", font_size=103, letter_spacing=-2.0, color=gimpcolor.RGB(0,0,0))

    ensure_file_exists(png_filepath)

    export_png(image, png_filepath)
    subprocess.call([aceit_path, png_filepath, ace_filepath, "-q"])
    os.remove(png_filepath)
