# Exports DK24 location sign .s and .sd files from Blender 4.2.

import bpy
import copy
import fileinput
import sys
import os

def to_filename(location):
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

def replace_text_in_file(file_path, search_exp, replace_exp):
    with open(file_path, 'r', encoding='utf-16') as file:
      file_text = file.read()
    file_text = file_text.replace(search_exp, replace_exp)
    with open(file_path, 'w', encoding='utf-16') as file:
      file.write(file_text)

def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def export_sd_file(file_path, shape_name):
    with open(file_path, 'w') as sd_file:
        sd_file.write('SIMISA@@@@@@@@@@JINX0t1t______\n')
        sd_file.write('Shape ( %s.s\n' % (shape_name))
        sd_file.write('\tESD_Detail_Level ( 0 )\n')
        sd_file.write('\tESD_Alternative_Texture ( 0 )\n')
        sd_file.write('\tESD_Bounding_Box ( -0.500000 -0.100000 -0.010000 0.500000 0.100000 0.010833 )\n')
        sd_file.write(')\n')

def export_s_file(file_path):
    bpy.ops.export.msts_s(filepath=file_path)


locations = ["Aarup", "Borup", "Ejby", "Elmelund", "Fjenneslev", "Forlev",
    "Fredericia", "Glostrup", "Helgoland", "Hellerup", "Hjulby", "Høje Taastrup",
    "Holmstrup", "Hvidovre", "Kalvebod", "Kastrup", "Kavslunde", "Klampenborg",
    "København H", "København G", "Korsør", "Marslev", "Middelfart", "Nyborg",
    "Odense", "Østerport", "Ringsted", "Roskilde", "Slagelse", "Snoghøj", "Sorø",
    "Sprogø", "Taulov", "Tommerup", "Ullerslev", "Valby", "Viby Sj.", "Vigerslev"]
material_name = "PGA_DKSign_Location_x"
export_path = "D:\\Games\\Open Rails\\Modelling\\DK24\\DKSign\\Location\\Export"

ensure_directory_exists(export_path)

for location in locations:
    shape_name = "PGA_DKSign_Location_%s" % (to_filename(location))
    texture_name = "PGA_DKSign_Location_%s" % (to_filename(location))
    s_filepath = "%s\\%s.s" % (export_path, shape_name)
    sd_filepath = "%s\\%s.sd" % (export_path, shape_name)

    export_sd_file(sd_filepath, shape_name)
    export_s_file(s_filepath)
    replace_text_in_file(s_filepath, "%s.ace" % (material_name), "%s.ace" % (texture_name))
