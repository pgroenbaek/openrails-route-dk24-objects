# Exports DK24 milepost textures as .png from GIMP 2.0 and bulk converts them to .ace via AceIt.

import os
import subprocess
from gimpfu import *

from_km = 0
to_km = 10
stepsize = 10
image_name = "PGA_DKMilepost_x_y.xcf"
export_path = "D:\\Games\\Open Rails\\3D Models\\DK24\\DKMilepost\\TextureExport"
aceit_path = "D:\\Games\\Open Rails\\Tools\\AceIt\\aceit.exe"

if not os.path.exists(export_path): 
    os.makedirs(export_path)

image = filter(lambda x: x.name == image_name, gimp.image_list())[0]
textlayer_km = filter(lambda x: x.name == "KM", image.layers)[0]
textlayer_m = filter(lambda x: x.name == "M", image.layers)[0]

for km in range(from_km, to_km + 1, stepsize):
    filename = "PGA_DKMilepost_%03d_%d" % (km, m)
    png_filepath = "%s\\%s.png" % (export_path, filename)
    ace_filepath = "%s\\%s.ace" % (export_path, filename)
    pdb.gimp_text_layer_set_text(textlayer_km, "%d" % (km))
    pdb.gimp_text_layer_set_font(textlayer_km, "NimbusSanL Bold")
    pdb.gimp_text_layer_set_color(textlayer_km, gimpcolor.RGB(0,0,0))
    pdb.gimp_text_layer_set_font_size(textlayer_km, 110, 0)
    pdb.gimp_text_layer_set_text(textlayer_m, "%d" % (m))
    pdb.gimp_text_layer_set_font(textlayer_m, "NimbusSanL Bold")
    pdb.gimp_text_layer_set_color(textlayer_m, gimpcolor.RGB(0,0,0))
    pdb.gimp_text_layer_set_font_size(textlayer_m, 73, 0)
    with open(png_filepath, 'w') as f:
        pass
    export_image = pdb.gimp_image_duplicate(image)
    export_layer = pdb.gimp_image_merge_visible_layers(export_image, CLIP_TO_IMAGE)
    pdb.gimp_file_save(export_image, export_layer, png_filepath, '?')
    pdb.gimp_image_delete(export_image)
    subprocess.call([aceit_path, png_filepath, ace_filepath, "-q"])
    os.remove(png_filepath)