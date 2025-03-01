# Exports DK24 ETCSL2 numbersign .s and .sd files from Blender 4.2.

import bpy
import copy
import fileinput
import sys
import os


def to_filename(signnumber):
    """
    Removes hyphens from a given string to create a filename-friendly format.

    Args:
        signnumber (str): The input string to process.

    Returns:
        str: A sanitized string with hyphens removed.
    """
    path_name = copy.deepcopy(signnumber)
    path_name = path_name.replace("-", "")
    return path_name


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
    Exports an SD (Shape Definition) file for MSTS/ORTS.

    Args:
        file_path (str): The destination file path for the SD file.
        shape_name (str): The name of the shape to be referenced in the file.
        bbox (str): The bounding box parameter to be specified in the file.
    """
    with open(file_path, 'w') as sd_file:
        sd_file.write('SIMISA@@@@@@@@@@JINX0t1t______\n')
        sd_file.write('Shape ( %s.s\n' % (shape_name))
        sd_file.write('\tESD_Detail_Level ( 0 )\n')
        sd_file.write('\tESD_Alternative_Texture ( 0 )\n')
        sd_file.write('\tESD_Bounding_Box ( %s )\n' % (bbox))
        sd_file.write(')\n')


def export_s_file(file_path):
    """
    Exports an S (Shape) file for ORTS using Blender's MSTS exporter.

    Args:
        file_path (str): The destination file path for the exported S file.
    """
    bpy.ops.export.msts_s(filepath=file_path)


marker_numbers = [x for xs in [
    ["Ig-%03d" % (x) for x in range(58, 59 + 1)],
    ["Ada-%03d" % (x) for x in range(11, 30 + 1)],
    ["Avh-%03d" % (x) for x in range(11, 56 + 1)],
    ["Bjs-%03d" % (x) for x in range(11, 52 + 1)],
    ["Kib-%03d" % (x) for x in range(7, 60 + 1)],
    ["Jsf-%03d" % (x) for x in range(11, 36 + 1)],
    ["Kjn-%03d" % (x) for x in range(11, 65 + 1)],
    ["Lel-%03d" % (x) for x in range(11, 53 + 1)],
    ["Rg-%03d" % (x) for x in range(114, 115 + 1)],
    # Guesswork for ny bane vestfyn (not real ones)
    ["Elm-%03d" % (x) for x in range(30, 40 + 1)],
    ["Rvb-%03d" % (x) for x in range(11, 60 + 1)],
    ["Spb-%03d" % (x) for x in range(11, 60 + 1)],
    ["Kel-%03d" % (x) for x in range(11, 60 + 1)],
    ["Anb-%03d" % (x) for x in range(11, 60 + 1)],
    ["Grm-%03d" % (x) for x in range(11, 60 + 1)],
    ["Sdh-%03d" % (x) for x in range(11, 60 + 1)],
    ["Ind-%03d" % (x) for x in range(11, 60 + 1)],
    ["Nra-%03d" % (x) for x in range(11, 60 + 1)],
    ["Ka-%03d" % (x) for x in range(40, 50 + 1)]
] for x in xs]

material_name = "PGA_DKSign_ETCSL2Number_x"
export_path = "D:\\Games\\Open Rails\\Modelling\\DK24\\Models\\DKSign\\ETCSL2\\Export"

ensure_directory_exists(export_path)

for n in marker_numbers:
    shape_name = "PGA_DKSign_ETCSL2Number_%s_R" % (to_filename(n))
    texture_name = "PGA_DKSign_ETCSL2Number_%s" % (to_filename(n))
    s_filepath = "%s\\%s.s" % (export_path, shape_name)
    sd_filepath = "%s\\%s.sd" % (export_path, shape_name)
    
    export_sd_file(sd_filepath, shape_name, "0.705000 3.955000 0.025000 0.375000 4.065000 0.045000")
    export_s_file(s_filepath)
    replace_text_in_file(s_filepath, "%s.ace" % (material_name), "%s.ace" % (texture_name))