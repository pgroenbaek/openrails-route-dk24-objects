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
# Do not run this manually, this script is called by `process_image_gimp.py`,
# which reads the JSON configuration and converts it into the positional arguments
# required by GIMP/Python-Fu. The `process_image_gimp.py` script that calls this
# script is run in Blender via `run_operations.py`.

from gimpfu import *
import os
import sys
import traceback


def ensure_directory_exists(path):
    """
    Ensures that the directory containing the output file exists.

    Args:
        path (str): Directory path to create.
    """
    if path and not os.path.exists(path):
        os.makedirs(path)


def python_fu_export_image_to_png(
    image,
    drawable,
    output_path,
    png_compression=9
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
    if not output_path:
        raise RuntimeError("GIMP PNG export requires 'output_path'.")

    if image is None:
        raise RuntimeError("GIMP PNG export requires an image.")

    try:
        png_compression = int(png_compression)
    except (TypeError, ValueError):
        png_compression = 9

    png_compression = max(0, min(9, png_compression))

    output_dir = os.path.dirname(output_path)

    ensure_directory_exists(output_dir)

    temporary_image = None

    try:
        temporary_image = pdb.gimp_image_duplicate(image)

        if temporary_image is None:
            raise RuntimeError("Could not duplicate the GIMP image.")

        merged_layer = pdb.gimp_image_merge_visible_layers(temporary_image, CLIP_TO_IMAGE)

        if merged_layer is None:
            raise RuntimeError("Could not merge the visible GIMP layers.")

        pdb.file_png_save(
            temporary_image,
            merged_layer,
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

        print("Image exported to PNG: %s with compression %d" % (output_path, png_compression))

    except Exception as e:
        print >> sys.stderr, (
            "Error exporting image to PNG '%s': %s" % (output_path, e)
        )
        traceback.print_exc()
        raise

    finally:
        if temporary_image is not None:
            try:
                pdb.gimp_image_delete(temporary_image)
            except Exception:
                pass


register(
    "python-fu-export-image-to-png",

    "Export Image to PNG",

    "Exports the current image to a PNG file "
    "with specified compression.",

    "Peter Grønbæk Andersen",
    "Peter Grønbæk Andersen",
    "2026",

    "<Image>/Python-Fu/MyScripts/Export PNG...",

    "*",

    [
        (
            PF_STRING,
            "output_path",
            "Output PNG Path",
            ""
        ),
        (
            PF_INT,
            "png_compression",
            "PNG Compression (0-9)",
            9
        )
    ],
    [],

    python_fu_export_image_to_png,
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