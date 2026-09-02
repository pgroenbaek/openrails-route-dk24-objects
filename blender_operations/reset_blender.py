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

# This is a Blender Python script.
#
# Do not run this manually, this script is called by `run_operations.py`,
# which reads the JSON configuration and dispatches the requested Blender
# operations as they are defined. The `run_operations.py` script can be run
# from the command line with Blender or directly from Blender's scripting
# console by pasting in the script with `CONFIG_FILES` configured.

import bpy
import addon_utils


EXPORTER_ADDON_MODULE_NAME = "io_export_mstsexporter_4-8-2"


def perform_operation(params):
    """
    Resets Blender to factory settings and checks for required addons. Any
    required addons are enabled. Any collections or objects loaded into
    Blender are also cleared.

    Args:
        params (dict): Configuration, not used.
    """
    bpy.ops.wm.read_factory_settings(use_empty=True)

    exporter_module = next(
        (addon for addon in addon_utils.modules()
        if addon.__name__ == EXPORTER_ADDON_MODULE_NAME),
        None
    )

    if exporter_module is None:
        raise RuntimeError(
            f"Required addon '{EXPORTER_ADDON_MODULE_NAME}' does not exist\n"
            "\tDownload this specific version from GitHub: "
            "https://github.com/pwillard/Blender_MSTS_ORTS_Exporter/releases/tag/4.8.1"
        )
    
    bpy.ops.preferences.addon_enable(module=EXPORTER_ADDON_MODULE_NAME)

