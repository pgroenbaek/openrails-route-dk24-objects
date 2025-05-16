# Exports DK24 milepost .s and .sd files from Blender 4.2.

import bpy
import fileinput
import sys


def replace_text_in_file(file_path, search_exp, replace_exp):
    """
    Replaces all occurrences of a given text in a file with a new text.

    Args:
        file_path (str): The path to the file to modify.
        search_exp (str): The text to search for in the file.
        replace_exp (str): The text to replace the search expression with.
    """
    with open(file_path, 'r', encoding='utf-16') as file:
        file_text = file.read()
    file_text = file_text.replace(search_exp, replace_exp)
    with open(file_path, 'w', encoding='utf-16') as file:
        file.write(file_text)


def ensure_directory_exists(path):
    """
    Ensures that a directory exists by creating it if necessary.

    Args:
        path (str): The directory path to check/create.
    """
    if not os.path.exists(path):
        os.makedirs(path)


def export_sd_file(file_path, shape_name, bbox):
    """
    Exports an SD (Shape Definition) file for ORTS.

    Args:
        file_path (str): The destination file path for the SD file.
        shape_name (str): The name of the shape to be referenced in the file.
        bbox (str): The bounding box parameter to be specified in the file.
    """
    with open(file_path, 'w') as sd_file:
        sd_file.write('SIMISA@@@@@@@@@@JINX0t1t______\n')
        sd_file.write(f'Shape ( {shape_name}.s\n')
        sd_file.write('\tESD_Detail_Level ( 0 )\n')
        sd_file.write('\tESD_Alternative_Texture ( 0 )\n')
        sd_file.write(f'\tESD_Bounding_Box ( {bbox} )\n')
        sd_file.write(')\n')


def export_s_file(file_path):
    """
    Exports an S (Shape) file for ORTS using Blender's MSTS exporter.

    Args:
        file_path (str): The destination file path for the exported S file.
    """
    bpy.ops.export.msts_s(filepath=file_path)


from_km = 0
to_km = 249
material_name = "PGA_DKMilepost_x_y"
texture_path = "D:/Games/Open Rails/Modelling/DK24/DKMilepost"
export_path = "D:/Games/Open Rails/Modelling/DK24/DKMilepost/Export"

ensure_directory_exists(export_path)

for km in range(from_km, to_km + 1):
    for m in [0, 2, 4, 6, 8]:
        shape_name = f"PGA_DKMilepost_{km:03d}_{m}"
        texture_name = f"PGA_DKMilepost_{km:03d}_{m}"
        s_filepath = f"{export_path}/{shape_name}.s"
        sd_filepath = f"{export_path}/{shape_name}.sd"

        export_sd_file(sd_filepath, shape_name, "-0.150000 0.000000 -0.025000 0.150000 1.900000 0.025000")
        export_s_file(s_filepath)
        replace_text_in_file(s_filepath, f"{material_name}.ace", f"{texture_name}.ace")
