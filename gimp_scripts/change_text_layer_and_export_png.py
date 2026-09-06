#!/usr/bin/env python
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

# This is a GIMP Python-fu script (Python 2).
#
# Do not run this manually, this script is called by `process_image_gimp.py`,
# which reads the JSON configuration and converts it into the positional arguments
# required by GIMP/Python-Fu. The `process_image_gimp.py` script that calls this
# script is run in Blender via `run_operations.py`.

from gimpfu import *
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
    if not isinstance(value, basestring):
        value = str(value)
    
    for old, new in replacements.items():
        value = value.replace(old, new)
    
    return value


def resolve_pattern_values(pattern, pattern_variables, is_filename=True):
    """
    Resolve a pattern into all possible concrete values.

    Args:
        pattern (str): Pattern containing placeholders such as `{variable}`.
        pattern_variables (dict): Variable definitions containing possible
            values and optional transformation rules.
        is_filename (bool): Whether the pattern is a filename. When False 
            the `filename_replacements` configuration is not applied.

    Returns:
        list[str]: All fully resolved pattern strings.
    """
    if not pattern_variables:
        return [pattern]

    formatter = string.Formatter()
    variable_names = list(dict.fromkeys(
        field_name
        for _, field_name, _, _ in formatter.parse(pattern)
        if field_name is not None
    ))

    if not variable_names:
        return [pattern]

    variable_value_lists = []

    for variable_name in variable_names:
        variable_config = pattern_variables.get(variable_name)

        if not variable_config:
            raise ValueError(
                "Pattern variable '%s' defined in pattern "
                "'%s' was not found in pattern_variables."
                % (variable_name, pattern)
            )

        variable_type = variable_config.get("type", "string")
        filename_replacements = variable_config.get("filename_replacements", {})

        if filename_replacements and variable_type != "string":
            raise ValueError(
                "Cannot use 'filename_replacements' in variable '%s' "
                "for variable types other than 'string'."
                % variable_name
            )

        values = []

        for value in variable_config["values"]:
            if isinstance(value, (int, long, float)):
                if variable_type != "number":
                    raise ValueError("Invalid value '%s' for value of type 'number'." % value)
                
                values.append(value)

            elif isinstance(value, basestring):
                if variable_type != "string":
                    raise ValueError("Invalid value '%s' for value of type 'string'." % value)

                if is_filename:
                    value = apply_filename_replacements(value, filename_replacements)

                values.append(value)

            elif isinstance(value, dict):
                number_start = value.get("number_start")
                number_stop = value.get("number_stop")
                number_step = value.get("number_step", 1)

                if number_start is None or number_stop is None:
                    raise ValueError(
                        "Invalid value expression in variable '%s', "
                        "missing 'number_start' or 'number_stop'."
                        % variable_name
                    )

                for number in range(number_start, number_stop + 1, number_step):
                    if "pattern" in value:
                        if variable_type != "string":
                            raise ValueError(
                                "Invalid value expression in variable '%s', "
                                "expressions cannot contain 'pattern' unless variable type is 'string'."
                                % variable_name
                            )

                        resolved_value = value["pattern"].format(number=number)

                        if is_filename:
                            resolved_value = apply_filename_replacements(resolved_value, filename_replacements)

                        values.append(resolved_value)
                    
                    else:
                        values.append(str(number) if variable_type == "string" else number)

            else:
                raise TypeError(
                    "Unsupported value type for variable '%s': %s"
                    % (variable_name, type(value).__name__)
                )

        variable_value_lists.append(values)

    return [
        pattern.format(**dict(zip(variable_names, combination)))
        for combination in itertools.product(*variable_value_lists)
    ]


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
    for layer in image.layers:
        if layer.name == text_layer_name and pdb.gimp_item_is_text_layer(layer):
            return layer

    return None


def set_text_layer_text(
    textlayer,
    text,
    font="Nimbus Sans Bold",
    font_size=48,
    letter_spacing=0,
    color=gimpcolor.RGB(0,0,0)
):
    """
    Sets the text and styling for a text layer in GIMP.

    Args:
        textlayer (gimp.Layer): The text layer to modify.
        text (str): The text to set for the layer.
        font (str, optional): The font to use for the text. Default is "NimbusSanL Bold".
        font_size (int, optional): The font size for the text. Default is 48.
        letter_spacing (int, optional): The letter spacing for the text. Default is 0.
        color (gimpcolor.RGB, optional): The color of the text. Default is black (RGB(0, 0, 0)).
    """
    pdb.gimp_text_layer_set_text(textlayer, text)
    pdb.gimp_text_layer_set_font(textlayer, font)
    pdb.gimp_text_layer_set_color(textlayer, color)
    pdb.gimp_text_layer_set_font_size(textlayer, font_size, 0)
    pdb.gimp_text_layer_set_letter_spacing(textlayer, letter_spacing)


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
        temporary_image = pdb.gimp_image_duplicate(image)

        if temporary_image is None:
            raise RuntimeError("Could not duplicate the GIMP image.")

        export_layer = pdb.gimp_image_merge_visible_layers(
            temporary_image,
            CLIP_TO_IMAGE
        )

        if export_layer is None:
            raise RuntimeError("Could not merge the visible GIMP layers.")

        pdb.gimp_file_save(
            temporary_image,
            export_layer,
            output_path,
            "?"
        )

    finally:
        if temporary_image is not None:
            try:
                pdb.gimp_image_delete(temporary_image)
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
        print >> sys.stderr, "Error: Invalid args JSON: %s" % e
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
        print >> sys.stderr, (
            "Warning: No 'pattern_variables' provided. "
            "Images will be exported without text and filename changes."
        )
    
    if not text_layer_replacements:
        print >> sys.stderr, (
            "Warning: No 'text_layer_replacements' provided. "
            "Images will be exported without text changes."
        )

    export_filenames = resolve_pattern_values(export_filename_pattern, pattern_variables)
    export_text_layer_replacements = {}
    export_text_layer_configs = {}

    for text_layer_replacement in text_layer_replacements:
        text_layer_name = text_layer_replacement.get("text_layer_name")
        text_layer_config = text_layer_replacement.get("text_layer_config", {})
        new_text_pattern = text_layer_replacement.get("new_text_pattern")

        if not text_layer_name:
            raise ValueError("Text layer replacement is missing 'new_text_pattern'.")
            
        if new_text_pattern:
            export_text_layer_texts = resolve_pattern_values(
                new_text_pattern,
                pattern_variables,
                is_filename=False
            )

        else:
            raise ValueError(
                "Text layer replacement with name '%s' is missing 'new_text_pattern'."
                % text_layer_name
            )
        
        if len(export_filenames) != len(export_text_layer_texts):
            raise ValueError(
                "Text layer '%s' produced %d text values, but "
                "%d export filenames were generated. "
                "The number of text values must match the number of export filenames."
                % (text_layer_name, len(export_text_layer_texts), len(export_filenames))
            )

        export_text_layer_replacements[text_layer_name] = export_text_layer_texts
        export_text_layer_configs[text_layer_name] = text_layer_config

    if export_folder:
        if not os.path.exists(export_folder):
            os.makedirs(export_folder)
    
    for idx, export_filename in enumerate(export_filenames):
        if not export_filename.endswith(".png"):
            export_filename = export_filename + ".png"
        
        export_path = export_folder + "/" + export_filename

        for text_layer_name in export_text_layer_replacements.keys():
            text_layer = find_text_layer(image, text_layer_name)

            if text_layer is None:
                print >> sys.stderr, (
                    "Warning: Text layer '%s' not found. "
                    "Cannot change text."
                    % text_layer_name
                )
                continue
            
            new_text = export_text_layer_replacements[text_layer_name][idx]
            text_layer_config = export_text_layer_configs[text_layer_name]

            set_text_layer_text(
                text_layer,
                new_text,
                font=text_layer_config.get("font", "Nimbus Sans Bold"),
                font_size=text_layer_config.get("font_size", 48),
                letter_spacing=text_layer_config.get("letter_spacing", 0.0),
                color=gimpcolor.RGB(*text_layer_config.get("color", [0, 0, 0]))
            )

            print("Text layer '%s' updated to: '%s'" % (text_layer_name, new_text))
        
        try:
            export_png(
                image,
                drawable,
                export_path,
                png_compression
            )

        except Exception as e:
            print >> sys.stderr, (
                "Error exporting image to PNG '%s': %s"
                % (export_path, e)
            )
            traceback.print_exc()
            raise

        print("Image exported: %s" % (export_path))



register(
    "python_fu_change_text_layer_and_export_png",

    "Change Text Layers and Export PNGs",

    "Iteratively changes text layers in an XCF image "
    "and exports multiple PNG files.",

    "Peter Grønbæk Andersen",
    "Peter Grønbæk Andersen",
    "2026",

    "<Image>/Python-Fu/MyScripts/"
    "Change Text Layers and Export PNGs...",

    "*",

    [
        (
            PF_STRING,
            "args",
            "Arguments passed to the script",
            ""
        )
    ],
    [],

    python_fu_change_text_layer_and_export_png,
    menu="/Python-Fu/MyScripts"
)


# IMPORTANT:
# Only start GIMP's plugin main loop when this file is executed
# as an actual plugin.
#
# `process_image_gimp.py`` executes this file inside an already
# running GIMP Python-Fu interpreter, so main() must NOT run there.

if __name__ == "__main__":
    main()