"""
Copyright (C) 2026 Peter Grønbæk Andersen <peter@grnbk.io>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

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


marker_numbers = [x for xs in [
    [f"Ig-{x:03d}" for x in range(58, 59 + 1)],
    [f"Ada-{x:03d}" for x in range(11, 30 + 1)],
    [f"Avh-{x:03d}" for x in range(11, 56 + 1)],
    [f"Bjs-{x:03d}" for x in range(11, 52 + 1)],
    [f"Kib-{x:03d}" for x in range(7, 60 + 1)],
    [f"Jsf-{x:03d}" for x in range(11, 36 + 1)],
    [f"Kjn-{x:03d}" for x in range(11, 65 + 1)],
    [f"Lel-{x:03d}" for x in range(11, 53 + 1)],
    [f"Rg-{x:03d}" for x in range(114, 115 + 1)],
] for x in xs]

material_name = "PGA_DKSign_ETCSL2Number_x"
export_path = "D:/Games/Open Rails/Modelling/DK24/Models/DKSign/ETCSL2/Export"

ensure_directory_exists(export_path)

for n in marker_numbers:
    shape_name = f"PGA_DKSign_ETCSL2Number_{to_filename(n)}_R"
    texture_name = f"PGA_DKSign_ETCSL2Number_{to_filename(n)}"
    s_filepath = f"{export_path}/{shape_name}.s"
    sd_filepath = f"{export_path}/{shape_name}.sd"
    
    export_sd_file(sd_filepath, shape_name, "0.705000 3.955000 0.025000 0.375000 4.065000 0.045000")
    export_s_file(s_filepath)
    replace_text_in_file(s_filepath, f"{material_name}.ace", f"{texture_name}.ace")