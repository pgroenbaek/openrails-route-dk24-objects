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


def to_filename(location):
    """
    Converts a given location string into a filename-friendly format.

    This function replaces special Scandinavian characters with their ASCII equivalents 
    and removes spaces and periods to create a filename-safe string.

    Args:
        location (str): The input string to convert.

    Returns:
        str: A sanitized string suitable for use as a filename.
    """
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


locations = ["Aarup", "Borup", "Ejby", "Fjenneslev", "Forlev",
    "Fredericia", "Glostrup", "Helgoland", "Hellerup", "Hjulby", "Høje Taastrup",
    "Holmstrup", "Hvidovre", "Kalvebod", "Kastrup", "Kavslunde", "Klampenborg",
    "København H", "København G", "Korsør", "Kværkeby", "Marslev", "Middelfart", "Nyborg",
    "Odense", "Østerport", "Ringsted", "Roskilde", "Slagelse", "Snoghøj", "Sorø",
    "Sprogø", "Taulov", "Tommerup", "Ullerslev", "Valby", "Viby Sj.", "Vigerslev"]
material_name = "PGA_DKSign_Location_x"
export_path = "D:/Games/Open Rails/Modelling/DK24/Models/DKSign/Location/Export"

ensure_directory_exists(export_path)

for location in locations:
    shape_name = f"PGA_DKSign_Location_{to_filename(location)}"
    texture_name = f"PGA_DKSign_Location_{to_filename(location)}"
    s_filepath = f"{export_path}/{shape_name}.s"
    sd_filepath = f"{export_path}/{shape_name}.sd"
    export_sd_file(sd_filepath, shape_name, "-0.5 -0.1 -0.0092 0.5 0.1 0.0108")
    export_s_file(s_filepath)
    replace_text_in_file(s_filepath, f"{material_name}.ace", f"{texture_name}.ace")
