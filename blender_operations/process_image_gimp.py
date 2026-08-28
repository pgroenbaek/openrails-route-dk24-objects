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
# configured with a set of config files and pasting it in.

import json
import subprocess
from pathlib import Path


def prepare_gimp_operations(gimp_operations):
    """
    Converts readable dictionary-style GIMP operation arguments
    into positional arguments expected by the configured
    Python functions.

    Args:
        gimp_operations (list): GIMP operation definitions.

    Returns:
        list: GIMP operations with positional argument lists.
    """
    prepared_operations = []

    for operation in gimp_operations:
        operation = operation.copy()

        args = operation.get("args", {})
        function_name = operation.get("function_name", "")

        if isinstance(args, list):
            prepared_operations.append(operation)
            continue

        if not isinstance(args, dict):
            raise ValueError(
                "GIMP operation 'args' must be either "
                "a dictionary or a list."
            )

        if function_name in "python-fu-change-text-layer":
            operation["args"] = [
                args.get("input_path", ""),
                args.get("output_path", ""),
                args.get("text_layer_name", ""),
                args.get("new_text", ""),
            ]

        elif function_name in "python-fu-export-image-to-png":
            operation["args"] = [
                args.get("output_path", ""),
                args.get("png_compression", 9),
            ]

        elif function_name in "python-fu-change-text-layer-and-export-png":
            export_config = args.get(
                "export_config",
                {}
            )

            operation["args"] = [
                args.get("base_output_dir", ""),
                json.dumps(export_config),
                args.get("png_compression", 9),
            ]

        else:
            raise ValueError(
                f"Unsupported GIMP function: {function_name}"
            )

        prepared_operations.append(operation)

    return prepared_operations


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
    input_file,
    operation,
):
    """
    Builds the Python code used to execute one custom GIMP script.

    Args:
        project_dir (Path): Project root directory.
        input_file (str): Input image path.
        operation (dict): Prepared GIMP operation.

    Returns:
        str: Python code for GIMP's batch interpreter.
    """
    input_path = resolve_project_path(
        project_dir,
        input_file,
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

    arguments.extend(
        gimp_python_argument(arg)
        for arg in args
    )

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
    input_file,
    gimp_operations,
):
    """
    Builds the command line used to launch GIMP in batch mode.

    Args:
        project_dir (Path): Project root directory.
        gimp_executable_path (str): GIMP executable.
        input_file (str): Input image path.
        gimp_operations (list): Prepared GIMP operations.

    Returns:
        list: Command arguments for subprocess.run().
    """
    command = [
        str(gimp_executable_path),
        "--no-interface",
        "--no-data",
        "--no-fonts",
        "--no-splash",
        "--batch-interpreter",
        "python-fu-eval",
    ]

    for operation in gimp_operations:
        operation_code = build_gimp_operation_code(
            project_dir,
            input_file,
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


def run_gimp_scripts(parameters):
    """
    Launches GIMP and executes the configured Python-Fu scripts.

    Args:
        parameters (dict):
            _project_dir (Path):
                Project root directory supplied by run_operations.py.

            input_file (str):
                Input image path relative to the project directory.

            output_file (str, optional):
                Common output path.

            gimp_operations (list):
                GIMP operation definitions.

            gimp_executable_path (str, optional):
                GIMP executable path. Defaults to "gimp".
    """
    project_dir = Path(parameters["_project_dir"]).resolve()

    input_file = parameters["input_file"]
    gimp_operations = parameters.get("gimp_operations",[],)
    gimp_executable_path = parameters.get("gimp_executable_path", "gimp")

    if isinstance(gimp_executable_path, Path):
        gimp_executable_path = str(gimp_executable_path)

    prepared_operations = prepare_gimp_operations(gimp_operations)

    command = build_gimp_command(
        project_dir,
        gimp_executable_path,
        input_file,
        prepared_operations,
    )

    if not command:
        raise RuntimeError("GIMP command is empty.")

    print(f"GIMP executable: {gimp_executable_path}")
    print(f"GIMP project directory: {project_dir}")
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


def perform_operation(parameters):
    """
    Performs GIMP image processing.

    Args:
        parameters (dict):
            _project_dir (Path):
                Project root directory supplied by run_operations.py.

            input_file (str):
                Input image path relative to the project directory.

            output_file (str, optional):
                Output path relative to the project directory.

            gimp_executable_path (str, optional):
                GIMP executable path.

            gimp_operations (list):
                GIMP operation definitions.
    """
    project_dir = Path(parameters["_project_dir"]).resolve()

    gimp_operations = parameters.get("gimp_operations", [])

    gimp_runner_params = {
        "_project_dir": project_dir,
        "input_file": parameters["input_file"],
        "output_file": parameters.get(
            "output_file"
        ),
        "gimp_operations": gimp_operations,
        "gimp_executable_path": parameters.get(
            "gimp_executable_path",
            "gimp",
        ),
    }

    print(
        "GIMP Processor: Running GIMP scripts "
        f"for input: {parameters['input_file']}"
    )

    run_gimp_scripts(gimp_runner_params)

    print("GIMP Processor: Finished GIMP script execution.")