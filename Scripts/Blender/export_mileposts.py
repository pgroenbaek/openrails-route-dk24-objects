# Exports DK24 milepost .s and .sd files from Blender 4.2.

import bpy
import fileinput
import sys

from_km = 231
to_km = 249
material = "PGA_DKMilepost_x_y"
texture_path = "D:\\Games\\Open Rails\\Modelling\\DK24\\DKMilepost"
export_path = "D:\\Games\\Open Rails\\Modelling\\DK24\\DKMilepost\\Export"

def replaceAll(filepath, search_exp, replace_exp):
    with open(filepath, 'r', encoding='utf-16') as file:
      filedata = file.read()
    filedata = filedata.replace(search_exp, replace_exp)
    with open(filepath, 'w', encoding='utf-16') as file:
      file.write(filedata)

if not os.path.exists(export_path): 
    os.makedirs(export_path)

for km in range(from_km, to_km + 1):
    for m in [0, 2, 4, 6, 8]:
        filename = "PGA_DKMilepost_%03d_%d" % (km, m)
        s_filepath = "%s\\%s.s" % (export_path, filename)
        sd_filepath = "%s\\%s.sd" % (export_path, filename)
        with open(sd_filepath, 'w') as sd_file:
            sd_file.write('SIMISA@@@@@@@@@@JINX0t1t______\n')
            sd_file.write('Shape ( %s.s\n' % (filename))
            sd_file.write('\tESD_Detail_Level ( 0 )\n')
            sd_file.write('\tESD_Alternative_Texture ( 0 )\n')
            sd_file.write('\tESD_Bounding_Box ( -0.150000 0.000000 -0.025000 0.150000 1.900000 0.025000 )\n')
            sd_file.write(')\n')
        bpy.ops.export.msts_s(filepath=s_filepath)
        replaceAll(s_filepath, "%s.ace" % (material), "%s.ace" % (filename))
