# Exports DK24 milepost .s and .sd files from Blender 4.2.

import bpy
import fileinput
import sys

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
        sd_file.write('\tESD_Bounding_Box ( -0.150000 0.000000 -0.025000 0.150000 1.900000 0.025000 )\n')
        sd_file.write(')\n')

def export_s_file(file_path):
    bpy.ops.export.msts_s(filepath=file_path)


from_km = 0
to_km = 249
material_name = "PGA_DKMilepost_x_y"
texture_path = "D:\\Games\\Open Rails\\Modelling\\DK24\\DKMilepost"
export_path = "D:\\Games\\Open Rails\\Modelling\\DK24\\DKMilepost\\Export"

ensure_directory_exists(export_path)

for km in range(from_km, to_km + 1):
    for m in [0, 2, 4, 6, 8]:
        shape_name = "PGA_DKMilepost_%03d_%d" % (km, m)
        texture_name = "PGA_DKMilepost_%03d_%d" % (km, m)
        s_filepath = "%s\\%s.s" % (export_path, shape_name)
        sd_filepath = "%s\\%s.sd" % (export_path, shape_name)

        export_sd_file(sd_filepath, shape_name)
        export_s_file(s_filepath)
        replace_text_in_file(s_filepath, "%s.ace" % (material_name), "%s.ace" % (texture_name))
