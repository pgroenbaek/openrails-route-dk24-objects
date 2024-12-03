# Exports DK24 ETCSL2 numbersign .s and .sd files from Blender 4.2.

import bpy
import copy
import fileinput
import sys
import os

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

material_name = "PGA_DKSign_ETCSL2Number_x"
export_path = "D:\\Games\\Open Rails\\Modelling\\DK24\\Models\\DKSign\\ETCSL2\\Export"
aceit_path = "D:\\Games\\Open Rails\\Tools\\AceIt\\aceit.exe"

def to_filename(signnumber):
    path_name = copy.deepcopy(signnumber)
    path_name = path_name.replace("-", "")
    return path_name

def replace_text_in_file(file_path, search_exp, replace_exp):
    with open(file_path, 'r', encoding='utf-16') as file:
      file_text = file.read()
    file_text = file_text.replace(search_exp, replace_exp)
    with open(file_path, 'w', encoding='utf-16') as file:
      file.write(file_text)

if not os.path.exists(export_path):
    os.makedirs(export_path)

for n in marker_numbers:
    file_name = "PGA_DKSign_ETCSL2Number_%s_L" % (to_filename(n))
    texture_name = "PGA_DKSign_ETCSL2Number_%s" % (to_filename(n))
    s_filepath = "%s\\%s.s" % (export_path, file_name)
    sd_filepath = "%s\\%s.sd" % (export_path, file_name)
    with open(sd_filepath, 'w') as sd_file:
        sd_file.write('SIMISA@@@@@@@@@@JINX0t1t______\n')
        sd_file.write('Shape ( %s.s\n' % (file_name))
        sd_file.write('\tESD_Detail_Level ( 0 )\n')
        sd_file.write('\tESD_Alternative_Texture ( 0 )\n')
        sd_file.write('\tESD_Bounding_Box ( -0.705000 3.955000 0.025000 -0.375000 4.065000 0.045000 )\n')
        sd_file.write(')\n')
    bpy.ops.export.msts_s(filepath=s_filepath)
    replace_text_in_file(s_filepath, "%s.ace" % (material_name), "%s.ace" % (texture_name))