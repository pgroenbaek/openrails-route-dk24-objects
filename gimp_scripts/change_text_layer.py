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

# This is a GIMP Python-fu operation script.
#
# It is called by `process_image_gimp.py`, which reads the human-readable
# JSON configuration and converts it into the positional arguments required
# by GIMP/Python-Fu. The `process_image_gimp.py` script is run in Blender
# via the `run_operations.py` script.

from gimpfu import *
import os
import sys
import traceback


def ensure_directory_exists(path):
    """
    Ensures that a directory exists by creating it if necessary.

    Args:
        path (str): Directory path to check or create.
    """
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def find_text_layer(image, text_layer_name):
    """
    Finds a text layer by exact name.

    Args:
        image (gimp.Image): GIMP image.
        text_layer_name (str): Exact name of the text layer.

    Returns:
        gimp.Layer or None
    """
    for layer in image.layers:
        if layer.name == text_layer_name and pdb.gimp_item_is_text_layer(layer):
            return layer

    return None


def python_fu_change_text_layer(
    image,
    drawable,
    output_path,
    text_layer_name,
    new_text
):
    """
    Changes the text of a specified text layer and saves the image.

    Args:
        image:
            Current GIMP image.

        drawable:
            Current GIMP drawable.

        output_path:
            Output image path.

        text_layer_name:
            Exact name of the text layer to modify.

        new_text:
            New text to put into the text layer.
    """
    if not text_layer_name:
        print("Error: 'text_layer_name' is required.", file=sys.stderr)
        return

    text_layer = find_text_layer(image, text_layer_name)

    if text_layer is None:
        print(
            "Warning: Text layer '%s' not found. Cannot change text."
            % text_layer_name,
            file=sys.stderr
        )
    else:
        try:
            pdb.gimp_text_layer_set_text(text_layer, new_text)

            print("Text layer '%s' updated to: '%s'"% (text_layer_name, new_text))

        except Exception as e:
            print(
                "Error changing text layer '%s': %s"
                % (text_layer_name, str(e)),
                file=sys.stderr
            )
            raise

    if not output_path:
        print("Error: 'output_path' is required.", file=sys.stderr)
        return

    try:
        output_dir = os.path.dirname(output_path)

        ensure_directory_exists(output_dir)

        pdb.gimp_file_save(
            RUN_NONINTERACTIVE,
            image,
            output_path,
            output_path
        )

        print("Image saved to: %s" % output_path)

    except Exception as e:
        print(
            "Error saving image '%s': %s"
            % (output_path, str(e)),
            file=sys.stderr
        )
        traceback.print_exc()
        raise


register(
    "python_fu_change_text_layer",

    "Change Text Layer in Image",

    "Changes the text content of a specified text layer "
    "in an image and saves the result.",

    "Peter Grønbæk Andersen",
    "Peter Grønbæk Andersen",
    "2026",

    "<Image>/Python-Fu/MyScripts/"
    "Change Text Layer...",

    "*",

    [
        (
            PF_STRING,
            "output_path",
            "Output Image Path",
            ""
        ),
        (
            PF_STRING,
            "text_layer_name",
            "Text Layer Name",
            ""
        ),
        (
            PF_STRING,
            "new_text",
            "New Text",
            ""
        )
    ],
    [],

    python_fu_change_text_layer,
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