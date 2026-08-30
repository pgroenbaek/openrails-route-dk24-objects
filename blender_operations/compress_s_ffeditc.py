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


FFEDITC_PATH = None
SUPPORTED_EXTENSIONS = (".s",)


def ensure_directory_exists(path):
    """
    Ensures that a directory exists by creating it if necessary.

    Args:
        path (str): Directory path to check or create.
    """
    os.makedirs(path, exist_ok=True)


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


def compress(input_path: str, output_path: str, ffeditc_exe_path: str) -> bool:
    """
    Compresses a file using the ffeditc_unicode.exe utility.

    Args:
        input_path (str): Path to the uncompressed input file.
        output_path (str): Path where the compressed file will be saved.
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
        "Running ffeditc_unicode: "
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
        - "ffeditc_path" (str): Path to the ffeditc_unicode.exe executable.
        - "export_path" (str, optional): Directory to use when resolving
          relative file paths or for output.
        - "file_path" (str, optional): Path to a single .s file.
        - "folder_path" (str, optional): Path to a folder containing .s
          files to process.
        - "_project_dir" (str, optional): Project directory used to resolve
          relative paths.
    """
    project_dir = params.get("_project_dir")
    ffeditc_path = params.get("ffeditc_path", FFEDITC_PATH)
    export_path = params.get("export_path")
    file_path = params.get("file_path")
    folder_path = params.get("folder_path")

    if not ffeditc_path:
        raise ValueError("No ffeditc_path specified.")

    if not project_dir:
        project_dir = os.getcwd()

    if not os.path.isabs(ffeditc_path):
        ffeditc_path = os.path.join(project_dir, ffeditc_path)

    source_file_paths = []

    if file_path and folder_path:
        raise ValueError("Cannot specify both 'file_path' and 'folder_path'.")

    elif file_path:
        source_file_paths.append(file_path)

    elif folder_path:
        if not os.path.isabs(folder_path):
            folder_path = os.path.join(project_dir, folder_path)

        if not os.path.isdir(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        for root, _, files in os.walk(folder_path):
            for filename in files:
                if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                    source_file_paths.append(os.path.join(root, filename))

    else:
        raise ValueError("No 'file_path' or 'folder_path' specified.")

    if export_path:
        if not os.path.isabs(export_path):
            export_path = os.path.join(project_dir, export_path)

        ensure_directory_exists(export_path)

    if not source_file_paths:
        print(f"No supported '.s' files found to process in '{folder_path}'")
        return

    for current_input_path in source_file_paths:
        if not os.path.isabs(current_input_path):
            if export_path:
                current_input_path = os.path.join(export_path, current_input_path)
            else:
                current_input_path = os.path.join(project_dir, current_input_path)

        if not os.path.isfile(current_input_path):
            raise FileNotFoundError(f"Source file not found: {current_input_path}")

        current_output_path = current_input_path

        compress(current_input_path, current_output_path, ffeditc_path)
