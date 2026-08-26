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
# It is called by `run_operations.py`, which reads the human-readable
# JSON configuration and dispatches the requested Blender operations.
# The `run_operations.py` script can also be run directly from Blender's
# Scripting Console configured with a set of config files.

import os
import platform
import subprocess


ACEIT_PATH = None
REMOVE_PNG = False


def ensure_directory_exists(path):
    """
    Ensures that a directory exists by creating it if necessary.

    Args:
        path (str): Directory path to check or create.
    """
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

    Args:
        params (dict): Export configuration.

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
                value = f"{prefix}-{number:{number_format}}"
                exports.append(
                    {
                        "prefix": prefix,
                        "number": number,
                        "value": value
                    }
                )

        return exports

    raise ValueError("No exports, values, or groups specified.")


def build_aceit_command(
    aceit_path,
    png_filepath,
    extra_params
):
    """
    Builds the command used to process a PNG file with AceIt.

    Args:
        aceit_path (str): Path to the AceIt executable.
        png_filepath (str): Path to the PNG file.
        extra_params (list): Additional AceIt command-line parameters.

    Returns:
        list: Complete AceIt command.
    """
    if platform.system() == "Windows":
        command = [
            aceit_path,
            png_filepath
        ]
    else:
        command = [
            "wine",
            aceit_path,
            png_filepath
        ]

    command.extend(
        str(param)
        for param in extra_params
    )

    return command


def process_png_file(
    aceit_path,
    png_filepath,
    extra_params
):
    """
    Processes a PNG file using AceIt.

    Args:
        aceit_path (str): Path to the AceIt executable.
        png_filepath (str): Path to the PNG file.
        extra_params (list): Additional AceIt command-line parameters.
    """
    command = build_aceit_command(
        aceit_path,
        png_filepath,
        extra_params
    )

    print(
        "Running AceIt: "
        + " ".join(
            f'"{part}"'
            if " " in part
            else part
            for part in command
        )
    )

    result = subprocess.call(command)

    if result != 0:
        raise RuntimeError(
            "AceIt failed with exit code "
            f"{result} for '{png_filepath}'."
        )


def perform_operation(params):
    """
    Processes one or more generated PNG files using AceIt.

    Args:
        params (dict): AceIt configuration.

    Expected keys include:
        - "aceit_path" (str): Path to the AceIt executable.
        - "export_path" (str): Directory containing PNG files.
        - "png_path" (str, optional): Path to a single PNG file.
        - "png_path_pattern" (str, optional): Pattern used to generate
          PNG paths.
        - "exports" (list, optional): Explicit export variable dictionaries.
        - "values" (list, optional): List of values used by filename patterns.
        - "groups" (list, optional): Groups used to generate numbered values.
        - "value_replacements" (dict, optional): String replacements applied
          to generated values.
        - "extra_params" (list, optional): Additional AceIt parameters.
        - "remove_png" (bool, optional): Whether to remove PNG files after
          successful AceIt processing.
        - "_project_dir" (str, optional): Project directory used to resolve
          relative paths.
    """
    project_dir = params.get("_project_dir")
    aceit_path = params.get("aceit_path", ACEIT_PATH)
    remove_png = params.get("remove_png", REMOVE_PNG)
    extra_params = params.get("extra_params", [])
    export_path = params.get("export_path")
    png_path = params.get("png_path")
    png_path_pattern = params.get("png_path_pattern")
    replacements = params.get("value_replacements", {})

    if not aceit_path:
        raise ValueError(
            "No aceit_path specified."
        )

    if not project_dir:
        project_dir = os.getcwd()

    if not os.path.isabs(aceit_path):
        aceit_path = os.path.join(project_dir, aceit_path)

    if not isinstance(extra_params, list):
        raise ValueError("'extra_params' must be a list.")

    if png_path:
        png_paths = [{"png_path": png_path}]

    elif png_path_pattern:
        exports = build_exports(params)

        png_paths = []

        for export in exports:
            values = {
                key: sanitize_value(
                    value,
                    replacements
                )
                for key, value in export.items()
            }

            current_png_path = (png_path_pattern.format(**values))

            png_paths.append(
                {
                    "png_path": current_png_path,
                    "values": values
                }
            )

    else:
        raise ValueError("No png_path or png_path_pattern specified.")

    if export_path:
        if not os.path.isabs(export_path):
            export_path = os.path.join(project_dir, export_path)

        ensure_directory_exists(export_path)

    for export in png_paths:
        current_png_path = export["png_path"]

        if not os.path.isabs(current_png_path):
            if export_path:
                current_png_path = os.path.join(export_path, current_png_path)
            else:
                current_png_path = os.path.join(project_dir, current_png_path)

        if not os.path.isfile(current_png_path):
            raise FileNotFoundError(f"PNG file not found: {current_png_path}")

        print(f"Processing PNG with AceIt: {current_png_path}")

        process_png_file(
            aceit_path,
            current_png_path,
            extra_params
        )

        if remove_png:
            os.remove(current_png_path)

            print(f"Removed PNG: {current_png_path}")