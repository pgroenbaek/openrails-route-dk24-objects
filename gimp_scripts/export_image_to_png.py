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
import traceback


def ensure_directory_exists(path):
    """
    Ensures that the directory containing the output file exists.

    Args:
        path (str): Directory path to create.
    """
    if path and not os.path.exists(path):
        os.makedirs(path)


def python_fu_export_image_to_png(image, drawable, args):
    """
    Exports the current GIMP image to PNG.

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
    export_filename = args.get("export_filename")
    png_compression = args.get("png_compression")

    if not export_folder:
        raise RuntimeError("GIMP PNG export requires 'export_folder'.")

    if not export_filename:
        raise RuntimeError("GIMP PNG export requires 'export_filename'.")

    if image is None:
        raise RuntimeError("GIMP PNG export requires an image.")

    try:
        png_compression = int(png_compression)
    except (TypeError, ValueError):
        png_compression = 9

    png_compression = max(0, min(9, png_compression))

    export_path = export_folder + "/" + export_filename

    ensure_directory_exists(export_folder)

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
            export_path,
            export_path,
            0,
            png_compression,
            0,
            0,
            0,
            0,
            0
        )

        print("Image exported to PNG: %s with compression %d" % (export_path, png_compression))

    except Exception as e:
        print >> sys.stderr, "Error exporting image to PNG '%s': %s" % (export_path, e)
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
            "args",
            "Arguments passed to the script",
            ""
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