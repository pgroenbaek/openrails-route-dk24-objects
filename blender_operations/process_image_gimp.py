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

import json
import itertools
import subprocess
from pathlib import Path


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


def generate_export_variables(variables_config):
    """
    Generates all possible combinations of variable values based on their configurations.
    Applies formatting and variable-specific replacements.

    Args:
        variables_config (dict): Dictionary defining each variable's generation rules.

    Returns:
        list: A list of dictionaries, where each dictionary represents one combination
              of variable assignments (e.g., [{"var1": "A", "var2": "001"}, ...]).
    """
    all_variable_values = {}
    for var_name, config in variables_config.items():
        values = []
        var_type = config.get("type", "string")
        var_format = config.get("format")
        var_replacements = config.get("replacements", {})

        if var_type == "integer":
            start = config["start"]
            stop = config["stop"]
            step = config.get("step", 1)
            for num in range(start, stop + 1, step):
                val = str(num)
                if var_format:
                    val = f"{num:{var_format}}"
                values.append(sanitize_value(val, var_replacements))
        elif var_type == "string":
            if "values" in config:
                for s_val in config["values"]:
                    values.append(sanitize_value(s_val, var_replacements))
            elif "segment_modifiers" in config:
                for modifier in config["segment_modifiers"]:
                    prefix = modifier.get("prefix", "")
                    start = modifier["start"]
                    stop = modifier["stop"]
                    step = modifier.get("step", 1)
                    mod_format = modifier.get("format", var_format)
                    for number in range(start, stop + 1, step):
                        val_part = str(number)
                        if mod_format:
                            val_part = f"{number:{mod_format}}"
                        full_val = f"{prefix}{val_part}"
                        values.append(sanitize_value(full_val, var_replacements))
            else:
                raise ValueError(
                    f"Variable '{var_name}' of type 'string' "
                    "must have 'values' or 'segment_modifiers'."
                )
        else:
            raise ValueError(f"Unsupported variable type for '{var_name}': {var_type}")
        all_variable_values[var_name] = values

    # Generate Cartesian product
    keys = list(all_variable_values.keys())
    product_lists = all_variable_values.values()

    combinations = []
    for combo_tuple in itertools.product(*product_lists):
        combo_dict = dict(zip(keys, combo_tuple))
        combinations.append(combo_dict)
    return combinations


def prepare_gimp_operation(operation_template, combo):
    """
    Converts a single readable dictionary-style GIMP operation argument
    into positional arguments expected by the configured Python functions,
    applying variable combinations to any patterns.

    Args:
        operation_template (dict): GIMP operation definition template.
        combo (dict): Dictionary of variable assignments for the current combination.

    Returns:
        dict: GIMP operation with positional argument lists and formatted values.
    """
    operation = operation_template.copy()

    # Format function_name if it contains patterns
    function_name = operation.get("function_name", "").format(**combo)
    operation["function_name"] = function_name

    args = operation.get("args", {})

    # If args is a dictionary, format its values. If it's a list, assume it's already processed or static.
    if isinstance(args, dict):
        formatted_args = {k: v.format(**combo) if isinstance(v, str) else v for k, v in args.items()}
        # Now convert to positional arguments based on function_name
        if function_name == "python-fu-change-text-layer":
            operation["args"] = [
                formatted_args.get("input_path", ""),
                formatted_args.get("output_path", ""),
                formatted_args.get("text_layer_name", ""),
                formatted_args.get("new_text", ""),
            ]
        elif function_name == "python-fu-export-image-to-png":
            operation["args"] = [
                formatted_args.get("output_path", ""),
                formatted_args.get("png_compression", 9),
            ]
        elif function_name == "python-fu-change-text-layer-and-export-png":
            export_config = formatted_args.get(
                "export_config",
                {}
            )
            if isinstance(export_config, dict):
                export_config = {k: v.format(**combo) if isinstance(v, str) else v for k, v in export_config.items()}

            operation["args"] = [
                formatted_args.get("base_output_dir", ""),
                json.dumps(export_config),
                formatted_args.get("png_compression", 9),
            ]
        else:
            raise ValueError(
                f"Unsupported GIMP function: {function_name}"
            )
    else:
        # If args is already a list, it should not contain patterns; if it does, it's an error.
        if any(isinstance(arg, str) and '{' in arg for arg in args):
             raise ValueError("GIMP operation 'args' as a list cannot contain patterns that need dynamic formatting. All pattern-based arguments must be provided in a dictionary.")
        operation["args"] = args

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


def run_gimp_scripts(params):
    """
    Launches GIMP and executes the configured Python-Fu scripts.

    Args:
        params (dict):
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
    project_dir = Path(params["_project_dir"]).resolve()

    input_file = params["input_file"]
    gimp_operations = params.get("gimp_operations",[],)
    gimp_executable_path = params.get("gimp_executable_path", "gimp")

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


def perform_operation(params):
    """
    Performs GIMP image processing using the configured GIMP operations for all
    combinations of defined variables.

    Args:
        params (dict): GIMP image processing configuration.

    Expected keys:
        - "_project_dir" (Path): Project root directory supplied by the
          operation runner.
        - "variables" (dict): Dictionary defining each variable's generation rules.
        - "input_file_pattern" (str): Pattern for the input image path relative
          to the project directory.
        - "output_file" (str, optional): Pattern for the output image path
          relative to the project directory.
        - "gimp_executable_path" (str, optional): Path to the GIMP executable.
        - "gimp_operations" (list): GIMP operation definition templates to
          execute on each generated input image.
    """
    project_dir = Path(params["_project_dir"]).resolve()
    variables_config = params.get("variables", {})
    input_file_pattern = params.get("input_file_pattern")
    gimp_operations_template = params.get("gimp_operations", [])
    gimp_executable_path = params.get("gimp_executable_path", "gimp")
    output_file_pattern = params.get("output_file")

    if not variables_config:
        raise ValueError("No 'variables' configuration specified for GIMP operation.")

    if not input_file_pattern:
        raise ValueError("No 'input_file_pattern' specified for GIMP operation.")

    variable_combinations = generate_export_variables(variables_config)

    for combo in variable_combinations:
        current_input_file = input_file_pattern.format(**combo)
        current_output_file = output_file_pattern.format(**combo) if output_file_pattern else None

        for operation_template in gimp_operations_template:
            prepared_op = prepare_gimp_operation(operation_template, combo)
            current_gimp_operations.append(prepared_op)

        gimp_runner_params = {
            "_project_dir": project_dir,
            "input_file": current_input_file,
            "output_file": current_output_file,
            "gimp_operations": current_gimp_operations,
            "gimp_executable_path": gimp_executable_path,
        }

        print(
            "GIMP Processor: Running GIMP scripts "
            f"for input: {current_input_file} with combo: {combo}"
        )

        run_gimp_scripts(gimp_runner_params)

    print("GIMP Processor: Finished all GIMP script executions.")
