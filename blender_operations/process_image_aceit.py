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
# It is called by `run_operations.py`, which reads the JSON configuration
# and dispatches the requested Blender operations. The `run_operations.py`
# script can also be run directly from Blender's scripting console
# configured with a set of config files by pasting it in.

import os
import platform
import subprocess


ACEIT_PATH = None
REMOVE_SOURCE_IMAGE = False
SUPPORTED_EXTENSIONS = (".dds", ".tga", ".jpg", ".bmp", ".tif", ".dib", ".png", ".ppm")


def ensure_directory_exists(path):
    """
    Ensures that a directory exists by creating it if necessary.

    Args:
        path (str): Directory path to check or create.
    """
    os.makedirs(path, exist_ok=True)


def build_aceit_command(
    aceit_path,
    image_filepath,
    extra_params
):
    """
    Builds the command used to process an image file with AceIt.

    Args:
        aceit_path (str): Path to the AceIt executable.
        image_filepath (str): Path to the image file.
        extra_params (list): Additional AceIt command-line parameters.

    Returns:
        list: Complete AceIt command.
    """
    if platform.system() == "Windows":
        command = [aceit_path, image_filepath]
    else:
        command = ["wine", aceit_path, image_filepath]

    command.extend([str(param) for param in extra_params])

    return command


def process_image_file(
    aceit_path,
    image_filepath,
    extra_params
):
    """
    Processes an image file using AceIt.

    Args:
        aceit_path (str): Path to the AceIt executable.
        image_filepath (str): Path to the image file.
        extra_params (list): Additional AceIt command-line parameters.
    """
    command = build_aceit_command(aceit_path, image_filepath, extra_params)

    print(
        "Running AceIt: "
        + " ".join(
            f'"{part}"'
            if " " in part
            else part
            for part in command
        )
    )

    try:
        subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"AceIt processing successful for '{image_filepath}'.")
    except subprocess.CalledProcessError as e:
        print(f"AceIt failed with exit code {e.returncode}")
        print("Error output:\n", e.stderr)
        raise RuntimeError(
            f"AceIt failed for '{image_filepath}'."
        ) from e
    except FileNotFoundError as e:
        print(f"Executable not found: {e}")
        raise FileNotFoundError(
            f"AceIt executable or a component not found for '{image_filepath}'."
        ) from e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise RuntimeError(
            f"An unexpected error occurred during AceIt processing for '{image_filepath}'."
        ) from e


def perform_operation(params):
    """
    Processes one or more image files using AceIt.

    Args:
        params (dict): AceIt configuration.

    Expected keys:
        - "aceit_path" (str): Path to the AceIt executable.
        - "export_path" (str, optional): Directory to use when resolving
          relative image paths.
        - "file_path" (str, optional): Path to a single image file.
        - "folder_path" (str, optional): Path to a folder containing image
          files to process.
        - "process_extensions" (list, optional): List of file extensions (e.g.,
          [".png", ".jpg"]) to process if a folder_path is specified. If not
          specified, all SUPPORTED_EXTENSIONS will be processed.
        - "extra_params" (list, optional): Additional AceIt parameters.
        - "remove_source_image" (bool, optional): Whether to remove source
          image files after successful AceIt processing.
        - "_project_dir" (str, optional): Project directory used to resolve
          relative paths.
    """
    project_dir = params.get("_project_dir")
    aceit_path = params.get("aceit_path", ACEIT_PATH)
    remove_source_image = params.get("remove_source_image", REMOVE_SOURCE_IMAGE)
    extra_params = params.get("extra_params", [])
    export_path = params.get("export_path")
    file_path = params.get("file_path")
    folder_path = params.get("folder_path")
    process_extensions = params.get("process_extensions")

    if not aceit_path:
        raise ValueError("No aceit_path specified.")

    allowed_extensions_set = set(ext.lower() for ext in SUPPORTED_EXTENSIONS)

    if process_extensions is not None:
        if not isinstance(process_extensions, list):
            raise ValueError("'process_extensions' must be a list of strings.")

        filtered_extensions = tuple(
            ext.lower() for ext in process_extensions
            if ext.lower() in allowed_extensions_set
        )

        if not filtered_extensions:
            raise ValueError(
                "None of the specified 'process_extensions' are supported. "
                f"Supported extensions are: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
        process_extensions = filtered_extensions
    else:
        process_extensions = SUPPORTED_EXTENSIONS

    if not project_dir:
        project_dir = os.getcwd()

    if not os.path.isabs(aceit_path):
        aceit_path = os.path.join(project_dir, aceit_path)

    if not isinstance(extra_params, list):
        raise ValueError("'extra_params' must be a list.")

    source_image_paths = []

    if file_path and folder_path:
        raise ValueError("Cannot specify both 'file_path' and 'folder_path'.")

    elif file_path:
        source_image_paths.append(file_path)

    elif folder_path:
        if not os.path.isabs(folder_path):
            folder_path = os.path.join(project_dir, folder_path)

        if not os.path.isdir(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        for root, _, files in os.walk(folder_path):
            for filename in files:
                if filename.lower().endswith(process_extensions):
                    source_image_paths.append(os.path.join(root, filename))

    else:
        raise ValueError("No 'file_path' or 'folder_path' specified.")

    if export_path:
        if not os.path.isabs(export_path):
            export_path = os.path.join(project_dir, export_path)

        ensure_directory_exists(export_path)

    if not source_image_paths:
        print(f"No supported image files found to process in '{folder_path}'")
        return

    for current_image_path in source_image_paths:
        if not os.path.isabs(current_image_path):
            if export_path:
                current_image_path = os.path.join(export_path, current_image_path)
            else:
                current_image_path = os.path.join(project_dir, current_image_path)

        if not os.path.isfile(current_image_path):
            raise FileNotFoundError(f"Source image file not found: {current_image_path}")

        print(f"Processing image with AceIt: {current_image_path}")

        process_image_file(aceit_path, current_image_path, extra_params)

        if remove_source_image:
            os.remove(current_image_path)

