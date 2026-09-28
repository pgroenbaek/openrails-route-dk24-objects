#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

# This is a GIMP 3.0 Python-Fu script (Python 3).
#
# Do not run this manually, this script is called by `process_image_gimp.py`,
# which reads the JSON configuration and converts it into the positional arguments
# required by GIMP/Python-Fu. The `process_image_gimp.py` script that calls this
# script is run in Blender via `run_operations.py`.

import gi

gi.require_version("Gimp", "3.0")

from gi.repository import Gimp, Gegl, Gio

import os
import sys
import json
import string
import itertools
import traceback


def apply_filename_replacements(value, replacements):
    """
    Applies a set of string replacements to a value.

    Args:
        value (str): The value to apply replacements to. Non-string values are
        converted to strings.
        replacements (dict[str, str]): A dictionary mapping substrings to their
        replacement values.

    Returns:
        str: The resulting string after all replacements have been applied.
    """
    if not isinstance(value, str):
        value = str(value)
    
    for old, new in replacements.items():
        value = value.replace(old, new)
    
    return value


def generate_variable_combinations(pattern_variables):
    """
    Generates all possible combinations of values for all defined pattern variables.

    Args:
        pattern_variables (dict): Variable definitions containing possible
            values and optional transformation rules.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary represents
        a unique combination of variable assignments (e.g., {'var1': 'value', 'var2': 1}).
    """
    if not pattern_variables:
        return [{}]

    all_variable_values = {}

    for variable_name, variable_config in pattern_variables.items():
        variable_type = variable_config.get("type", "string")

        values = []
        for value_def in variable_config["values"]:
            if isinstance(value_def, (int, float)):
                if variable_type != "number":
                    raise ValueError(f"Invalid value '{value_def}' for value of type 'number'.")
                
                values.append(value_def)
            
            elif isinstance(value_def, str):
                if variable_type != "string":
                    raise ValueError(f"Invalid value '{value_def}' for value of type 'string'.")
                
                values.append(value_def)
            
            elif isinstance(value_def, dict):
                number_start = value_def.get("number_start")
                number_stop = value_def.get("number_stop")
                number_step = value_def.get("number_step", 1)

                if number_start is None or number_stop is None:
                    raise ValueError(
                        f"Invalid value expression in variable '{variable_name}', "
                        "missing 'number_start' or 'number_stop'."
                    )

                for number in range(number_start, number_stop + 1, number_step):
                    if "pattern" in value_def:
                        if variable_type != "string":
                            raise ValueError(
                                f"Invalid value expression in variable '{variable_name}', "
                                "expressions cannot contain 'pattern' unless variable type is 'string'."
                            )

                        resolved_value = value_def["pattern"].format(number=number)
                        values.append(resolved_value)
                    else:
                        values.append(str(number) if variable_type == "string" else number)
            else:
                raise TypeError(
                    f"Unsupported value type for variable '{variable_name}': {type(value_def).__name__}"
                )
        all_variable_values[variable_name] = values

    variable_names = sorted(all_variable_values.keys())

    if not variable_names:
        return [{}]
    
    sorted_value_lists = [all_variable_values[name] for name in variable_names]

    all_combinations = []

    for combination_tuple in itertools.product(*sorted_value_lists):
        combination_dict = dict(zip(variable_names, combination_tuple))
        all_combinations.append(combination_dict)
    
    return all_combinations


def format_pattern_with_combination(pattern, combination_dict):
    """
    Formats a pattern string using the provided variable combination.

    Args:
        pattern (str): The pattern string with placeholders.
        combination_dict (dict): A dictionary mapping variable names to their values
                                 for a specific combination.

    Returns:
        str: The formatted string.
    """
    return pattern.format(**combination_dict)


def find_text_layer(image, text_layer_name):
    """
    Finds a text layer by exact name.

    Args:
        image:
            Current GIMP image.

        text_layer_name:
            Exact name of the text layer.

    Returns:
        GIMP text layer or None.
    """
    for layer in image.get_layers():
        if layer.get_name() == text_layer_name and isinstance(layer, Gimp.TextLayer):
            return layer

    return None


def set_text_layer_text(
    textlayer,
    text,
    font="Nimbus Sans Bold",
    font_size=48,
    letter_spacing=0,
    color=None
):
    """
    Sets the text and styling for a text layer in GIMP.

    Args:
        textlayer (Gimp.TextLayer): The text layer to modify.
        text (str): The text to set for the layer.
        font (str, optional): The font to use for the text. Default is "Nimbus Sans Bold".
        font_size (int, optional): The font size for the text. Default is 48.
        letter_spacing (int, optional): The letter spacing for the text. Default is 0.
        color (Gegl.Color, optional): The color of the text. Default is black.
    """
    if color is None:
        color = Gegl.Color.new("black")

    textlayer.set_text(text)
    textlayer.set_font(Gimp.Font.get_by_name(font))
    textlayer.set_color(color)
    textlayer.set_font_size(font_size, Gimp.Unit.pixel())
    textlayer.set_letter_spacing(letter_spacing)


def export_png(image, drawable, output_path, png_compression):
    """
    Exports the current GIMP image to a PNG file.

    The image is duplicated before export so that merging visible layers
    does not modify the original image. The visible layers of the duplicate
    are merged and the resulting image is saved to the specified output path.

    Args:
        image:
            GIMP image to export.

        drawable:
            Currently active drawable. Included for compatibility with
            the GIMP file-saving API.

        output_path (str):
            Full path to the output PNG file.

        png_compression (int):
            PNG compression level from 0 to 9.

    Raises:
        RuntimeError:
            If the image cannot be duplicated or the visible layers cannot
            be merged.
    """
    temporary_image = None

    try:
        temporary_image = image.duplicate()

        if temporary_image is None:
            raise RuntimeError("Could not duplicate the GIMP image.")

        export_layer = temporary_image.merge_visible_layers(
            Gimp.MergeType.CLIP_TO_IMAGE
        )

        if export_layer is None:
            raise RuntimeError("Could not merge the visible GIMP layers.")

        pdb = Gimp.get_pdb()
        export_procedure = pdb.lookup_procedure("file-png-export")

        if export_procedure is None:
            raise RuntimeError("Could not find GIMP PNG export procedure.")

        export_config = export_procedure.create_config()

        export_config.set_property(
            "run-mode",
            Gimp.RunMode.NONINTERACTIVE
        )

        export_config.set_property(
            "image",
            temporary_image
        )

        export_config.set_property(
            "file",
            Gio.File.new_for_path(output_path)
        )

        export_config.set_property(
            "options",
            None
        )

        export_config.set_property(
            "interlaced",
            False
        )

        export_config.set_property(
            "compression",
            png_compression
        )

        result = export_procedure.run(export_config)

        status = result.index(0)

        if status != Gimp.PDBStatusType.SUCCESS:
            error = pdb.get_last_error()

            if error:
                raise RuntimeError(f"PNG export failed: {error}")

            raise RuntimeError(f"PNG export failed with status: {status}")

    finally:
        if temporary_image is not None:
            try:
                temporary_image.delete()
            except Exception:
                pass


def python_fu_change_text_layer_and_export_png(image, drawable, args):
    """
    Changes text layers in an XCF image based on a configuration
    and exports multiple PNGs.

    Args:
        image:
            Current GIMP image.

        drawable:
            Current GIMP drawable.

        args:
            Arguments passed to the script.
    """
    try:
        args = json.loads(args)

    except (ValueError, TypeError) as e:
        print(f"Error: Invalid args JSON: {e}", file=sys.stderr)
        raise

    export_folder = args.get("export_folder")
    export_filename_pattern = args.get("export_filename_pattern")
    text_layer_replacements = args.get("text_layer_replacements", {})
    pattern_variables = args.get("pattern_variables", {})
    png_compression = args.get("png_compression", 9)

    if not export_folder:
        raise ValueError("Parameter 'export_folder' is required.")

    if not export_filename_pattern:
        raise ValueError("Parameter 'export_filename_pattern' is required.")
    
    if not pattern_variables:
        print(
            "Warning: No 'pattern_variables' provided. "
            "Images will be exported without text and filename changes.",
            file=sys.stderr
        )
    
    if not text_layer_replacements:
        print(
            "Warning: No 'text_layer_replacements' provided. "
            "Images will be exported without text changes.",
            file=sys.stderr
        )

    all_combinations = generate_variable_combinations(pattern_variables)

    if not all_combinations:
        print(
            "Warning: No combinations of pattern variables generated. No images will be exported.",
            file=sys.stderr
        )
        return


    text_layer_patterns_map = {}
    export_text_layer_configs = {}
    
    for text_layer_replacement in text_layer_replacements:
        text_layer_name = text_layer_replacement.get("text_layer_name")
        text_layer_config = text_layer_replacement.get("text_layer_config", {})
        new_text_pattern = text_layer_replacement.get("new_text_pattern")

        if not text_layer_name:
            raise ValueError("Text layer replacement is missing 'text_layer_name'.")
        
        if not new_text_pattern:
            raise ValueError(
                f"Text layer replacement with name '{text_layer_name}' is missing 'new_text_pattern'."
            )
        
        text_layer_patterns_map[text_layer_name] = new_text_pattern
        export_text_layer_configs[text_layer_name] = text_layer_config

    resolved_export_filenames = []
    resolved_text_layer_texts_by_name = {
        name: [] for name in text_layer_patterns_map.keys()
    }

    for combination_dict in all_combinations:
        filename_format_dict = {}
        for var_name, var_value in combination_dict.items():
            current_var_config = pattern_variables.get(var_name, {})
            filename_replacements = current_var_config.get("filename_replacements", {})
            
            if isinstance(var_value, str) and filename_replacements:
                filename_format_dict[var_name] = apply_filename_replacements(
                    var_value,
                    filename_replacements
                )
            else:
                filename_format_dict[var_name] = var_value

        resolved_filename = format_pattern_with_combination(
            export_filename_pattern,
            filename_format_dict
        )
        resolved_export_filenames.append(resolved_filename)

        for text_layer_name, new_text_pattern in text_layer_patterns_map.items():
            resolved_text = format_pattern_with_combination(
                new_text_pattern,
                combination_dict
            )
            resolved_text_layer_texts_by_name[text_layer_name].append(resolved_text)

    if export_folder:
        if not os.path.exists(export_folder):
            os.makedirs(export_folder)
    
    for idx, export_filename in enumerate(resolved_export_filenames):
        if not export_filename.endswith(".png"):
            export_filename = export_filename + ".png"
        
        export_path = os.path.join(export_folder, export_filename)

        for text_layer_name, text_values_for_layer in resolved_text_layer_texts_by_name.items():
            text_layer = find_text_layer(image, text_layer_name)

            if text_layer is None:
                print(
                    f"Warning: Text layer '{text_layer_name}' not found. Cannot change text.",
                    file=sys.stderr
                )
                continue
            
            new_text = text_values_for_layer[idx]
            text_layer_config = export_text_layer_configs[text_layer_name]

            color_values = text_layer_config.get("color", [0, 0, 0])
            color = Gegl.Color.new(
                f"rgba("
                f"{color_values[0] / 255.0},"
                f"{color_values[1] / 255.0},"
                f"{color_values[2] / 255.0},"
                "1.0)"
            )

            set_text_layer_text(
                text_layer,
                new_text,
                font=text_layer_config.get("font", "Nimbus Sans Bold"),
                font_size=text_layer_config.get("font_size", 48),
                letter_spacing=text_layer_config.get("letter_spacing", 0.0),
                color=color
            )

            print(f"Text layer '{text_layer_name}' updated to: '{new_text}'")
        
        try:
            export_png(
                image,
                drawable,
                export_path,
                png_compression
            )

        except Exception as e:
            print(
                f"Error exporting image to PNG '{export_path}': {e}",
                file=sys.stderr
            )
            traceback.print_exc()
            raise

        print(f"Image exported: {export_path}")