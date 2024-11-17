# Exports DK24 location sign textures as .png from GIMP 2.0 and bulk converts them to .ace via AceIt.

import os
import subprocess
from gimpfu import *

locations = ["Aarup", "Borup", "Ejby", "Elmelund", "Fjenneslev", "Forlev",
    "Fredericia", "Glostrup", "Helgoland", "Hellerup", "Høje Taastrup",
    "Holmstrup", "Hvidovre", "Kalvebod", "Kastrup", "Kavslunde", "Klampenborg",
    "København H", "København G", "Korsør", "Marslev", "Middelfart", "Nyborg",
    "Odense", "Østerport", "Ringsted", "Roskilde", "Slagelse", "Snoghøj", "Sorø",
    "Sprogø", "Taulov", "Tommerup", "Ullerslev", "Valby", "Viby Sj.", "Vigerslev"]
image_name = "PGA_DKSign_Location_x.xcf"
export_path = "D:\\Games\\Open Rails\\3D Models\\DK24\\DKSign\\Location\\TextureExport"
aceit_path = "D:\\Games\\Open Rails\\Tools\\AceIt\\aceit.exe"

def toPathName(location):
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

if not os.path.exists(export_path): 
    os.makedirs(export_path)

image = filter(lambda x: x.name == image_name, gimp.image_list())[0]
textlayer_l = filter(lambda x: x.name == "L", image.layers)[0]

for location in locations:
    filename = "PGA_DKSign_Location_%s" % (toPathName(location))
    png_filepath = "%s\\%s.png" % (export_path, filename)
    ace_filepath = "%s\\%s.ace" % (export_path, filename)
    pdb.gimp_text_layer_set_text(textlayer_l, "%s" % (location))
    pdb.gimp_text_layer_set_font(textlayer_l, "NimbusSanL Bold")
    pdb.gimp_text_layer_set_color(textlayer_l, gimpcolor.RGB(0,0,0))
    pdb.gimp_text_layer_set_letter_spacing(textlayer_l, -2.0)
    pdb.gimp_text_layer_set_font_size(textlayer_l, 103, 0)
    with open(png_filepath, 'w') as f:
        pass
    export_image = pdb.gimp_image_duplicate(image)
    export_layer = pdb.gimp_image_merge_visible_layers(export_image, CLIP_TO_IMAGE)
    pdb.gimp_file_save(export_image, export_layer, png_filepath, '?')
    pdb.gimp_image_delete(export_image)
    subprocess.call([aceit_path, png_filepath, ace_filepath, "-q"])
    os.remove(png_filepath)