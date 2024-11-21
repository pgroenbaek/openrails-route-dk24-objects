# Exports DK24 ETCSL2 numbersign textures as .png from GIMP 2.0 and bulk converts them to .ace via AceIt.

import os
import subprocess
from gimpfu import *

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
export_path = "D:\\Games\\Open Rails\\Modelling\\DK24\\Models\\DKSign\\ETCSL2\\TextureExport"
aceit_path = "D:\\Games\\Open Rails\\Tools\\AceIt\\aceit.exe"

def toPathName(signnumber):
    path_name = copy.deepcopy(signnumber)
    path_name = path_name.replace("-", "")
    return path_name

if not os.path.exists(export_path): 
    os.makedirs(export_path)

image = filter(lambda x: x.name == image_name, gimp.image_list())[0]
textlayer_n = filter(lambda x: x.name == "N", image.layers)[0]

for n in marker_numbers:
        filename = "PGA_DKSign_ETCSL2Number_%s" % (n.replace("-", ""))
        png_filepath = "%s\\%s.png" % (export_path, filename)
        ace_filepath = "%s\\%s.ace" % (export_path, filename)
        pdb.gimp_text_layer_set_text(textlayer_n, "%s" % (n))
        pdb.gimp_text_layer_set_font(textlayer_n, "NimbusSanL Bold")
        pdb.gimp_text_layer_set_color(textlayer_n, gimpcolor.RGB(0,0,0))
        pdb.gimp_text_layer_set_font_size(textlayer_n, 120, 0)
        pdb.gimp_text_layer_set_letter_spacing(textlayer_n, -4.0)
        with open(png_filepath, 'w') as f:
            pass
        export_image = pdb.gimp_image_duplicate(image)
        export_layer = pdb.gimp_image_merge_visible_layers(export_image, CLIP_TO_IMAGE)
        pdb.gimp_file_save(export_image, export_layer, png_filepath, '?')
        pdb.gimp_image_delete(export_image)
        subprocess.call([aceit_path, png_filepath, ace_filepath, "-q"])
        os.remove(png_filepath)