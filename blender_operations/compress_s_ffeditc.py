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


SUPPORTED_EXTENSIONS = (".s",)


def wine_path(path):
    """
    Convert a Unix filesystem path to its Windows equivalent using Wine.

    Args:
        path: The Unix filesystem path to convert.

    Returns:
        The corresponding Windows-style path as understood by Wine.

    Raises:
        subprocess.CalledProcessError: If the winepath command fails.
    """
    result = subprocess.run(
        ["winepath", "-w", path],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def compress_shape(input_path: str, output_path: str, ffeditc_exe_path: str) -> bool:
    """
    Compresses a shape using the ffeditc_unicode.exe utility.

    Args:
        input_path (str): Path to the uncompressed input shape file.
        output_path (str): Path where the compressed shape will be saved.
        ffeditc_exe_path (str): Path to the ffeditc_unicode.exe executable.

    Raises:
        FileNotFoundError: If the input file or the specified ffeditc_unicode.exe is not found.
        OSError: If file operations fail.

    Returns:
        bool: True if compression succeeded, False otherwise.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"No such file or directory: '{input_path}'")

    output_dir = os.path.dirname(output_path)

    if not os.path.isdir(output_dir):
        ensure_directory_exists(output_dir)

    if not os.path.exists(ffeditc_exe_path):
        raise FileNotFoundError(f"No such file or directory: '{ffeditc_exe_path}'")

    executable_dir = os.path.dirname(ffeditc_exe_path)

    if platform.system() == "Windows":
        command = [
            ffeditc_exe_path,
            input_path,
            "/c",
            "/o:" + output_path
        ]
    else:
        wine_input_path = wine_path(input_path)
        wine_output_path = wine_path(output_path)

        command = [
            "wine",
            ffeditc_exe_path,
            wine_input_path,
            "/c",
            "/o:" + wine_output_path,
        ]

    print(
        "Running ffeditc_unicode.exe: "
        + " ".join(
            f'"{part}"'
            if " " in part
            else part
            for part in command
        )
    )

    try:
        result = subprocess.run(
            command,
            cwd=executable_dir,
            capture_output=True,
            text=True,
            check=True
        )
        print("Compression successful.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print("Error output:\n", e.stderr)
        return False
    except FileNotFoundError as e:
        print(f"Executable not found: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


def perform_operation(params):
    """
    Compresses one or more .s files using ffeditc_unicode.exe.

    Args:
        params (dict): Compression configuration.

    Expected keys:
        - "ffeditc_exe_path" (str): Path to the ffeditc_unicode.exe executable.
        - "shape_folder" (str): Path to a folder containing .s
          files to process.
        - "shape_filename" (str, optional): Path to a single .s file.
        - "_project_dir" (str, optional): Project directory used to resolve
          relative paths.
    """
    ffeditc_exe_path = params.get("ffeditc_exe_path")
    shape_folder = params.get("shape_folder")
    shape_filename = params.get("shape_filename")
    project_dir = params.get("_project_dir")

    if not ffeditc_exe_path:
        raise ValueError("No 'ffeditc_exe_path' parameter specified.")

    if shape_folder and not os.path.isabs(shape_folder):
        shape_folder = project_dir / shape_folder

    shape_files = []

    if shape_filename:
        shape_file = shape_folder / shape_filename
        shape_files.append(shape_file)

    elif shape_folder:
        if not os.path.isdir(shape_folder):
            raise FileNotFoundError(f"Folder not found: {shape_folder}")

        for root, _, files in os.walk(shape_folder):
            for filename in files:
                if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                    shape_files.append(os.path.join(root, filename))

    else:
        raise ValueError("No 'shape_filename' or 'shape_folder' specified.")

    if not shape_files:
        print(f"No supported '.s' files found to process in '{shape_folder}'")
        return

    for shape_file in shape_files:
        if not os.path.isabs(shape_file):
            shape_file = os.path.join(project_dir, shape_file)

        if not os.path.isfile(shape_file):
            raise FileNotFoundError(f"Shape file not found: {shape_file}")

        compress_shape(shape_file, shape_file, ffeditc_exe_path)
