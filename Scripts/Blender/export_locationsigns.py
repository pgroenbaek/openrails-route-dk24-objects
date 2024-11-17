# Exports DK24 location sign .s and .sd files from Blender 4.2.

import bpy
import copy
import fileinput
import sys
import os

locations = ["Aarup", "Borup", "Ejby", "Elmelund", "Fjenneslev", "Forlev",
    "Fredericia", "Glostrup", "Helgoland", "Hellerup", "Høje Taastrup",
    "Holmstrup", "Hvidovre", "Kalvebod", "Kastrup", "Kavslunde", "Klampenborg",
    "København H", "København G", "Korsør", "Marslev", "Middelfart", "Nyborg",
    "Odense", "Østerport", "Ringsted", "Roskilde", "Slagelse", "Snoghøj", "Sorø",
    "Sprogø", "Taulov", "Tommerup", "Ullerslev", "Valby", "Viby Sj.", "Vigerslev"]
material = "PGA_DKSign_Location_x"
texture_path = "D:\\Games\\Open Rails\\3D Models\\DK24\\DKSign\\Location"
export_path = "D:\\Games\\Open Rails\\3D Models\\DK24\\DKSign\\Location\\Export"

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

def replaceAll(filepath, search_exp, replace_exp):
    with open(filepath, 'r', encoding='utf-16') as file:
      filedata = file.read()
    filedata = filedata.replace(search_exp, replace_exp)
    with open(filepath, 'w', encoding='utf-16') as file:
      file.write(filedata)

if not os.path.exists(export_path): 
    os.makedirs(export_path)

for location in locations:
    filename = "PGA_DKSign_Location_%s" % (toPathName(location))
    s_filepath = "%s\\%s.s" % (export_path, filename)
    sd_filepath = "%s\\%s.sd" % (export_path, filename)
    with open(sd_filepath, 'w') as sd_file:
        sd_file.write('SIMISA@@@@@@@@@@JINX0t1t______\n')
        sd_file.write('Shape ( %s.s\n' % (filename))
        sd_file.write('\tESD_Detail_Level ( 0 )\n')
        sd_file.write('\tESD_Alternative_Texture ( 0 )\n')
        sd_file.write('\tESD_Bounding_Box ( -0.500000 -0.100000 -0.010000 0.500000 0.100000 0.010833 )\n')
        sd_file.write(')\n')
    bpy.ops.export.msts_s(filepath=s_filepath)
    replaceAll(s_filepath, "%s.ace" % (material), "%s.ace" % (filename))
