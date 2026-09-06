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
# which reads the JSON configuration and processes the requested Blender
# operations as they are defined. The `run_operations.py` script can be run
# from the command line with Blender or directly from Blender's scripting
# console by pasting in the script with `CONFIG_FILES` configured.

import os
import platform
import subprocess
from pathlib import Path


SUPPORTED_EXTENSIONS = (".dds", ".tga", ".jpg", ".bmp", ".tif", ".dib", ".png", ".ppm")


def build_aceit_command(
    aceit_executable_path,
    image_filepath,
):
    """
    Builds the command used to process an image file with AceIt.

    Args:
        aceit_executable_path (str): Path to the AceIt executable.
        image_filepath (str): Path to the image file.

    Returns:
        list: Complete AceIt command.
    """
    if platform.system() == "Windows":
        command = [aceit_executable_path, image_filepath, "-q"]
    else:
        command = ["wine", aceit_executable_path, image_filepath, "-q"]

    return command


def process_image_file(
    aceit_executable_path,
    image_filepath
):
    """
    Processes an image file using AceIt.

    Args:
        aceit_executable_path (str): Path to the AceIt executable.
        image_filepath (str): Path to the image file.
    """
    command = build_aceit_command(aceit_executable_path, image_filepath)

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
        - "aceit_executable_path" (str): Path to the AceIt executable.
        - "image_folder" (str): Path to a folder containing image
          files to process.
        - "image_filename" (str, optional): Path to a single image file.
        - "process_extensions" (list, optional): List of file extensions (e.g.,
          [".png", ".jpg"]) to process if only a folder_path is specified. If not
          specified, all SUPPORTED_EXTENSIONS will be processed.
        - "remove_source_image" (bool, optional): Whether to remove source
          image files after successful AceIt processing.
        - "_project_dir" (str, optional): Project directory used to resolve
          relative paths.
    """
    image_folder = Path(params.get("image_folder"))
    image_filename = params.get("image_filename")
    remove_source_image = params.get("remove_source_image", False)
    process_extensions = params.get("process_extensions")
    aceit_executable_path = params.get("aceit_executable_path")
    project_dir = Path(params.get("_project_dir"))

    if not aceit_executable_path:
        raise ValueError("No 'aceit_executable_path' parameter specified.")

    if image_folder and not os.path.isabs(image_folder):
        image_folder = project_dir / image_folder
    
    allowed_extensions_set = set(ext.lower() for ext in SUPPORTED_EXTENSIONS)

    if process_extensions is not None:
        if not isinstance(process_extensions, list):
            raise ValueError("Parameter 'process_extensions' must be a list of strings.")

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

    image_files = []

    if image_filename:
        image_file = image_folder / image_filename
        image_files.append(str(image_file))

    elif image_folder:
        if not os.path.isdir(image_folder):
            raise FileNotFoundError(f"Folder not found: {image_folder}")

        for root, _, files in os.walk(image_folder):
            for filename in files:
                if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                    image_files.append(os.path.join(root, filename))

    else:
        raise ValueError("No 'image_filename' or 'image_folder' specified.")

    if not image_files:
        print(f"No supported image files found to process in '{shape_folder}'")
        return

    for image_file in image_files:
        if not os.path.isabs(image_file):
            image_file = os.path.join(project_dir, image_file)

        if not os.path.isfile(image_file):
            raise FileNotFoundError(f"Image file not found: {image_file}")

        process_image_file(aceit_executable_path, image_file)

        if remove_source_image:
            os.remove(image_file)