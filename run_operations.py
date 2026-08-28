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

# This is the Blender operation runner.
#
# It reads the human-readable JSON configuration and dispatches
# the requested Blender operation scripts with their parameters.
# It can be run from the command line with Blender or directly
# from Blender's Scripting Console.

import bpy
import json
import sys
import argparse
import importlib
import addon_utils
from pathlib import Path
from mathutils import Vector


PROJECT_DIR = Path(r"/media/peter/T7 Shield/Repos/personal/openrails-route-dk24-objects")

CONFIG_FILES = [
    #PROJECT_DIR / "configs" / "dk_wire" / "PGA_DKWire_Odense_162_7.json",
]

OPERATIONS_DIR = PROJECT_DIR / "blender_operations"


def run_operations_from_config(config_file_path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    addon_module = "io_export_mstsexporter_4-8-2"
    module = next(
        (addon for addon in addon_utils.modules()
        if addon.__name__ == addon_module),
        None
    )
    if module is None:
        raise RuntimeError(
            f"Required addon '{addon_module}' does not exist\n"
            "\tDownload it from GitHub: "
            "https://github.com/pwillard/Blender_MSTS_ORTS_Exporter/releases/tag/4.8.1"
        )
    bpy.ops.preferences.addon_enable(module=addon_module)
    config_file_path = Path(config_file_path).resolve()
    operations_dir = Path(OPERATIONS_DIR).resolve()
    if str(operations_dir) not in sys.path:
        sys.path.insert(0, str(operations_dir))
    try:
        with open(config_file_path, "r", encoding="utf-8") as f:
            operations_config = json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_file_path}")
        return (False, "Config File Not Found")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {config_file_path}")
        print(f"Line {e.lineno}, column {e.colno}: {e.msg}")
        return (False, "Config JSON Error")
    if not isinstance(operations_config, list):
        print("Error: Configuration file must contain a JSON list.")
        return (False, "Config Format Error")
    for op_data in operations_config:
        if not isinstance(op_data, dict):
            print(f"Skipping invalid operation: {op_data}")
            continue
        op_type = op_data.get("operation_type")
        parameters = op_data.get("parameters", {})
        parameters["_project_dir"] = PROJECT_DIR
        if not op_type:
            print(f"Skipping operation due to missing 'operation_type': {op_data}")
            continue
        print(f"\n--- Running operation: {op_type} ---")
        try:
            module_name = op_type.lower()
            operation_module = importlib.import_module(module_name)
            operation_module = importlib.reload(operation_module)
            operation_function = getattr(operation_module, "perform_operation", None)
            if operation_function is None:
                print(f"Error: Module '{module_name}.py' does not have a 'perform_operation' function.")
                continue
            operation_function(parameters)
            print(f"Operation '{op_type}' completed successfully.")
        except ModuleNotFoundError as e:
            print(f"Error: Operation module '{module_name}.py' not found.")
            print(f"Details: {e}")
            return (False, op_type)
        except AttributeError as e:
            print(f"Error calling operation '{op_type}': {e}")
            return (False, op_type)
        except Exception as e:
            print(f"An unexpected error occurred during operation '{op_type}': {e}")
            import traceback
            traceback.print_exc()
            return (False, op_type)
    return (True, None)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run Blender operations from JSON configuration files.")
    parser.add_argument(
        "--config",
        action="append",
        help="Path to a JSON configuration file. Can be specified multiple times."
    )
    if "--" in sys.argv:
        script_args = sys.argv[sys.argv.index("--") + 1:]
    else:
        script_args = []
    return parser.parse_args(script_args)


if __name__ == "__main__":
    args = parse_arguments()
    if args.config:
        config_files = [Path(config) for config in args.config]
    else:
        config_files = CONFIG_FILES
    failed_configs = []
    print("=" * 60)
    print("Blender Operation Runner")
    print("=" * 60)
    print(f"Project directory: {PROJECT_DIR}")
    print(f"Operations directory: {OPERATIONS_DIR}")
    print(f"Blender version: {bpy.app.version_string}")
    print(f"Config files to process: {len(config_files)}")
    print("=" * 60)
    for index, config_file in enumerate(config_files, start=1):
        print("\n" + "=" * 60)
        print(f"CONFIG {index}/{len(config_files)}")
        print(f"Running: {config_file}")
        print("=" * 60)
        success_status, failed_step = run_operations_from_config(config_file)
        if not success_status:
            failed_configs.append((config_file, failed_step))
            print(f"Config FAILED: {config_file} (failed at step: {failed_step})")
        else:
            print(f"Config COMPLETED: {config_file}")
    print("\n" + "=" * 60)
    print("All config files processed.")
    if failed_configs:
        print("\n" + "=" * 60)
        print("SUMMARY OF FAILED CONFIGURATIONS:")
        print("=" * 60)
        for config_path, failed_step_name in failed_configs:
            print(f"- {config_path} (failed at step: {failed_step_name})")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("All configurations ran successfully!")
        print("=" * 60)
