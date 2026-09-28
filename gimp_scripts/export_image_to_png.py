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

from gi.repository import Gimp, Gio

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
        print(f"Error: Invalid args JSON: {e}", file=sys.stderr)
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

    export_path = os.path.join(export_folder, export_filename)

    ensure_directory_exists(export_folder)

    temporary_image = None

    try:
        temporary_image = image.duplicate()

        if temporary_image is None:
            raise RuntimeError("Could not duplicate the GIMP image.")

        merged_layer = temporary_image.merge_visible_layers(
            Gimp.MergeType.CLIP_TO_IMAGE
        )

        if merged_layer is None:
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
            Gio.File.new_for_path(export_path)
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

        print(f"Image exported to PNG: {export_path} with compression {png_compression}")

    except Exception as e:
        print(
            f"Error exporting image to PNG '{export_path}': {e}",
            file=sys.stderr
        )
        traceback.print_exc()
        raise

    finally:
        if temporary_image is not None:
            try:
                temporary_image.delete()
            except Exception:
                pass