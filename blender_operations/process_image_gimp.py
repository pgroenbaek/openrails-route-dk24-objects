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
import json
import itertools
import subprocess
from pathlib import Path


SUPPORTED_EXTENSIONS = (".xcf",)


def prepare_gimp_operation_args(operation_template):
    """
    Converts a GIMP operation's arguments to a JSON string.

    Args:
        operation_template: GIMP operation definition containing an ``args``
            dictionary.

    Returns:
        A copy of the GIMP operation with ``args`` serialized as JSON.
    """
    operation = operation_template.copy()

    args = operation.get("args", {})

    if not isinstance(args, str):
        operation["args"] = json.dumps(args)

    return operation


def resolve_project_path(project_dir, file_path):
    """
    Resolves a path relative to the project directory.

    Args:
        project_dir (Path): Project root directory.
        file_path (str or Path): Relative or absolute path.

    Returns:
        Path: Resolved absolute path.
    """
    file_path = Path(file_path)

    if file_path.is_absolute():
        return file_path.resolve()

    return (project_dir / file_path).resolve()


def escape_gimp_string(value):
    """
    Escapes a string for inclusion in the Python code passed
    to GIMP's batch interpreter.

    Args:
        value: Value to escape.

    Returns:
        str: Escaped string.
    """
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


def gimp_python_argument(value):
    """
    Converts a Python value into a Python literal suitable for
    inclusion in the GIMP batch command.

    Args:
        value: Value to convert.

    Returns:
        str: Python literal.
    """
    if isinstance(value, bool):
        return "True" if value else "False"

    if isinstance(value, (int, float)):
        return str(value)

    if value is None:
        return "None"

    return f'"{escape_gimp_string(value)}"'


def get_python_function_name(function_name):
    """
    Converts a configured function name into the Python function
    name defined by the custom GIMP script.

    Args:
        function_name (str): Configured function name.

    Returns:
        str: Python function name.
    """
    return function_name.replace("-", "_")


def build_gimp_operation_code(
    project_dir,
    image_file,
    operation,
):
    """
    Builds the Python code used to execute one custom GIMP script.

    Args:
        project_dir (Path): Project root directory.
        image_file (str): Input image path.
        operation (dict): Prepared GIMP operation.

    Returns:
        str: Python code for GIMP's batch interpreter.
    """
    input_path = resolve_project_path(
        project_dir,
        image_file,
    )

    script_name = operation.get("script_name")

    if not script_name:
        raise ValueError("GIMP operation is missing 'script_name'.")

    script_path = resolve_project_path(
        project_dir / "gimp_scripts",
        script_name,
    )

    if not script_path.exists():
        raise FileNotFoundError(f"GIMP script not found: {script_path}")

    function_name = operation["function_name"]
    python_function_name = get_python_function_name(function_name)

    args = operation.get("args", [])

    arguments = [
        "img",
        "pdb.gimp_image_get_active_drawable(img)",
    ]

    arguments.append(gimp_python_argument(args))

    script_namespace = (
        "{"
        "'__name__': '__gimp_batch_script__', "
        "'__file__': "
        f"{gimp_python_argument(str(script_path))}"
        "}"
    )

    return (
        "img = pdb.gimp_file_load("
        f"{gimp_python_argument(str(input_path))}, "
        f"{gimp_python_argument(str(input_path))}"
        "); "

        f"script_namespace = {script_namespace}; "

        f"exec(compile("
        f"open("
        f"{gimp_python_argument(str(script_path))}"
        ").read(), "
        f"{gimp_python_argument(str(script_path))}, "
        "'exec'), script_namespace); "

        f"script_namespace["
        f"{gimp_python_argument(python_function_name)}"
        "]("
        f"{', '.join(arguments)}"
        ")"
    )


def build_gimp_command(
    project_dir,
    gimp_executable_path,
    image_file,
    gimp_operations,
):
    """
    Builds the command line used to launch GIMP in batch mode.

    Args:
        project_dir (Path): Project root directory.
        gimp_executable_path (str): GIMP executable.
        image_file (str): Input image path.
        gimp_operations (list): Prepared GIMP operations.

    Returns:
        list: Command arguments for subprocess.run().
    """
    command = [
        str(gimp_executable_path),
        "--no-interface",
        "--no-data",
        "--no-splash",
        "--batch-interpreter",
        "python-fu-eval",
    ]

    for operation in gimp_operations:
        operation_code = build_gimp_operation_code(
            project_dir,
            image_file,
            operation,
        )

        command.extend([
            "--batch",
            operation_code,
        ])

    command.extend([
        "--batch",
        "pdb.gimp_quit(1)",
    ])

    return command


def run_gimp_scripts(params):
    """
    Launches GIMP and executes the configured Python-Fu scripts.

    Args:
        params (dict):
            _project_dir (Path):
                Project root directory supplied by run_operations.py.

            image_file (str):
                Input image path relative to the project directory.

            gimp_operations (list):
                GIMP operation definitions.

            gimp_executable_path (str, optional):
                GIMP executable path. Defaults to "gimp".
    """
    project_dir = Path(params["_project_dir"]).resolve()

    image_file = params["image_file"]
    gimp_operations = params.get("gimp_operations",[],)
    gimp_executable_path = params.get("gimp_executable_path", "gimp")

    if isinstance(gimp_executable_path, Path):
        gimp_executable_path = str(gimp_executable_path)

    command = build_gimp_command(
        project_dir,
        gimp_executable_path,
        image_file,
        gimp_operations,
    )

    if not command:
        raise RuntimeError("GIMP command is empty.")

    print(f"GIMP executable: '{gimp_executable_path}'")
    print(f"GIMP project directory: '{project_dir}'")
    print()
    print("GIMP command:")
    print()
    print(
        " ".join(
            gimp_python_argument(arg)
            if isinstance(arg, str)
            else str(arg)
            for arg in command
        )
    )
    print()

    if command[0] != gimp_executable_path:
        raise RuntimeError(
            "GIMP command was constructed incorrectly.\n"
            f"Expected executable: {gimp_executable_path}\n"
            f"Actual command[0]: {command[0]}"
        )

    print("GIMP Processor: Starting GIMP...")

    try:
        result = subprocess.run(
            command,
            cwd=str(project_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

    except FileNotFoundError as exc:
        raise RuntimeError(
            f"GIMP executable not found: "
            f"{gimp_executable_path}"
        ) from exc

    except PermissionError as exc:
        raise RuntimeError(
            "Permission denied while launching GIMP.\n"
            f"Executable: {gimp_executable_path}\n"
            f"Command[0]: {command[0]}\n"
            f"Working directory: {project_dir}"
        ) from exc

    if result.stdout:
        print(result.stdout, end="")

    stderr_lines = []

    if result.stderr:
        ignore_lines = [
            "Two different plugins tried to register",
            "  gimp.main(None, None, _query, _run)",
        ]

        for line in result.stderr.splitlines(keepends=True):
            if not any([ignored in line for ignored in ignore_lines]):
                stderr_lines.append(line)

    filtered_stderr = "".join(stderr_lines)

    if filtered_stderr:
        print(filtered_stderr, end="")

    error_markers = [
        "batch command experienced an execution error",
        "batch command experienced a calling error",
        "Traceback (most recent call last):",
        "gimp.error:",
        "GIMP-Error:",
        "NameError:",
        "TypeError:",
        "SyntaxError:",
        "KeyError:",
        "FileNotFoundError:",
        "PermissionError:",
        "Procedure",
        "Plug-in crashed:",
        "returned no return values",
    ]

    detected_errors = [
        marker
        for marker in error_markers
        if marker in result.stderr
    ]

    if result.returncode != 0:
        raise RuntimeError(
            f"GIMP exited with error code "
            f"{result.returncode}"
        )

    if detected_errors:
        raise RuntimeError(
            "GIMP reported an error while "
            "executing the batch commands."
        )

    print("GIMP Processor: GIMP completed successfully.")


def perform_operation(params):
    """
    Performs GIMP image processing using the configured GIMP operations for all
    combinations of defined variables.

    Args:
        params (dict): GIMP image processing configuration.

    Expected keys:
        - "image_folder" (str): Path to a folder containing image
          files to process.
        - "image_filename" (str, optional): Path to a single image file.
          relative to the project directory.
        - "process_extensions" (list, optional): List of file extensions (e.g.,
          [".xcf"]) to process if only a folder_path is specified. If not
        - "gimp_executable_path" (str, optional): Path to the GIMP executable.
        - "gimp_operations" (list): GIMP operation definition templates to
          execute on each generated input image.
        - "_project_dir" (str): Project root directory supplied by the
          operation runner.
    """
    image_folder = params.get("image_folder")
    image_filename = params.get("image_filename")
    process_extensions = params.get("process_extensions")
    gimp_operations = params.get("gimp_operations", [])
    gimp_executable_path = params.get("gimp_executable_path", "gimp")
    project_dir = Path(params["_project_dir"]).resolve()

    if not gimp_executable_path:
        raise ValueError("No 'gimp_executable_path' parameter specified.")

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
        gimp_operations_to_execute = []

        for operation_template in gimp_operations:
            prepared_op = prepare_gimp_operation_args(operation_template)
            gimp_operations_to_execute.append(prepared_op)

        gimp_runner_params = {
            "_project_dir": project_dir,
            "image_file": image_file,
            "gimp_operations": gimp_operations_to_execute,
            "gimp_executable_path": gimp_executable_path,
        }

        print(f"GIMP Processor: Running GIMP scripts for input: '{image_file}'")

        run_gimp_scripts(gimp_runner_params)

    print("GIMP Processor: Finished all GIMP script executions.")
