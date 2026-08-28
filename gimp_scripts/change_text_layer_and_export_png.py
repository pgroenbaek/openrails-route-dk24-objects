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

# This is a GIMP Python-fu script.
#
# It is called by `process_image_gimp.py`, which reads the JSON configuration
# and converts it into the positional arguments required by GIMP/Python-Fu.
# The `process_image_gimp.py` script is run in Blender via the
# `run_operations.py` script.

from gimpfu import *
import os
import sys
import json
import traceback


def ensure_directory_exists(path):
    """
    Ensures that a directory exists by creating it if necessary.

    Args:
        path (str): Directory path to check or create.
    """
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def sanitize_value(value, replacements):
    """
    Applies configured string replacements to a value.

    Args:
        value (str): Value to sanitize.
        replacements (dict): Mapping of strings to replacement strings.

    Returns:
        str: Sanitized value.
    """
    value = str(value)

    for search, replace in replacements.items():
        value = value.replace(search, replace)

    return value


def build_exports(params):
    """
    Builds the list of exports from the operation parameters.

    Supported formats:

        "exports": [
            {"value": "foo"},
            {"value": "bar"}
        ]

    or:

        "values": [
            "foo",
            "bar"
        ]

    or:

        "groups": [
            {
                "prefix": "DK-Gantry-Fe",
                "start": 1,
                "stop": 3,
                "step": 1,
                "number_format": "03d"
            }
        ]

    Returns:
        list: List of dictionaries containing export variables.
    """

    exports = params.get("exports")

    if exports is not None:
        return exports

    values = params.get("values")

    if values is not None:
        return [
            {
                "value": value
            }
            for value in values
        ]

    groups = params.get("groups")

    if groups is not None:
        exports = []

        for group in groups:
            prefix = group.get("prefix", "")
            start = group["start"]
            stop = group["stop"]
            step = group.get("step", 1)
            number_format = group.get("number_format", "03d")

            for number in range(start, stop + 1, step):
                exports.append(
                    {
                        "prefix": prefix,
                        "number": number,
                        "value": f"{prefix}-{number:{number_format}}"
                    }
                )

        return exports

    raise ValueError("No exports, values, or groups specified.")


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


def export_png(
    image,
    drawable,
    output_path,
    png_compression
):
    """
    Exports the current GIMP image to PNG.

    Args:
        image:
            Current GIMP image.

        drawable:
            Current GIMP drawable.

        output_path:
            Full output PNG path.

        png_compression:
            PNG compression level from 0 to 9.
    """
    ensure_directory_exists(os.path.dirname(output_path))

    png_compression = max(0, min(9, int(png_compression)))

    pdb.file_png_save(
        image,
        drawable,
        output_path,
        output_path,
        0,
        png_compression,
        0,
        0,
        0,
        0,
        0
    )

    print("  Image exported to PNG: %s with compression %d" % (output_path, png_compression))


def python_fu_change_text_layer_and_export_png(
    image,
    drawable,
    base_output_dir,
    export_config_json_str,
    png_compression=9
):
    """
    Changes text layers in an XCF image based on a configuration
    and exports multiple PNGs.

    Args:
        image:
            Current GIMP image.

        drawable:
            Current GIMP drawable.

        base_output_dir:
            Base directory where exported PNG files are saved.

        export_config_json_str:
            JSON string containing the export configuration.

        png_compression:
            PNG compression level from 0 to 9.
    """
    try:
        export_config = json.loads(export_config_json_str)

    except (ValueError, TypeError) as e:
        print("Error: Invalid export configuration JSON: %s" % e, file=sys.stderr)
        raise

    replacements = export_config.get("value_replacements", {})
    output_filename_pattern = export_config.get("output_filename_pattern")
    text_layers_config = export_config.get("text_layers_config", [])

    if not output_filename_pattern:
        raise ValueError("'output_filename_pattern' is required in export_config.")

    if not text_layers_config:
        print(
            "Warning: No 'text_layers_config' provided. "
            "Images will be exported without text changes.",
            file=sys.stderr
        )

    exports = build_exports(export_config)

    for export_index, export_vars in enumerate(exports, start=1):
        current_values = {
            key: sanitize_value(
                value,
                replacements
            )
            for key, value in export_vars.items()
        }

        print("Processing export %d with values: %s" % (export_index, current_values))

        try:
            relative_output_filename = output_filename_pattern.format(**current_values)

        except KeyError as e:
            print(
                "Error formatting output filename. "
                "Missing value: %s"
                % e,
                file=sys.stderr
            )
            raise

        full_output_file_path = os.path.join(base_output_dir, relative_output_filename)

        ensure_directory_exists(os.path.dirname(full_output_file_path))

        for config in text_layers_config:
            text_layer_name_pattern = config.get("text_layer_name_pattern")
            new_text_pattern = config.get("new_text_pattern")

            if not text_layer_name_pattern or not new_text_pattern:
                print(
                    "Warning: Skipping malformed "
                    "text_layer_config: %s"
                    % config,
                    file=sys.stderr
                )
                continue

            try:
                text_layer_name = text_layer_name_pattern.format(**current_values)
                new_text = new_text_pattern.format(**current_values)

            except KeyError as e:
                print(
                    "Warning: Could not format text layer "
                    "configuration. Missing value: %s"
                    % e,
                    file=sys.stderr
                )
                raise

            text_layer = find_text_layer(image, text_layer_name)

            if text_layer is None:
                print(
                    "Warning: Text layer '%s' not found. "
                    "Cannot change text."
                    % text_layer_name,
                    file=sys.stderr
                )
                continue

            pdb.gimp_text_layer_set_text(text_layer, new_text)

            print("  Text layer '%s' updated to: '%s'" % (text_layer_name, new_text))

        try:
            export_png(
                image,
                drawable,
                full_output_file_path,
                png_compression
            )

        except Exception as e:
            print("Error exporting image to PNG '%s': %s" % (full_output_file_path, e), file=sys.stderr)

            traceback.print_exc()
            raise

        print("Completed export %d: %s" % (export_index, full_output_file_path))


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
            "base_output_dir",
            "Base Output Directory",
            ""
        ),
        (
            PF_STRING,
            "export_config_json_str",
            "Export Configuration (JSON)",
            "{}"
        ),
        (
            PF_INT,
            "png_compression",
            "PNG Compression (0-9)",
            9
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