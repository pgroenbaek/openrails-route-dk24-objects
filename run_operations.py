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

import bpy
import json
import sys
import argparse
import importlib
from pathlib import Path
from mathutils import Vector


PROJECT_DIR = Path(r"/media/peter/T7 Shield/Repos/personal/openrails-route-dk24-objects")

CONFIG_FILES = [
    PROJECT_DIR / "configs" / "dk_gantry" / "PGA_DKGantry_Fe.json",
]

OPERATIONS_DIR = PROJECT_DIR / "blender_operations"


def run_operations_from_config(config_file_path):
    config_file_path = Path(config_file_path).resolve()
    operations_dir = Path(OPERATIONS_DIR).resolve()
    if str(operations_dir) not in sys.path:
        sys.path.insert(0, str(operations_dir))
    try:
        with open(config_file_path, "r", encoding="utf-8") as f:
            operations_config = json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_file_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {config_file_path}")
        print(f"Line {e.lineno}, column {e.colno}: {e.msg}")
        return False
    if not isinstance(operations_config, list):
        print("Error: Configuration file must contain a JSON list.")
        return False
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
        except AttributeError as e:
            print(f"Error calling operation '{op_type}': {e}")
        except Exception as e:
            print(f"An unexpected error occurred during operation '{op_type}': {e}")
            import traceback
            traceback.print_exc()
    return True


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run Blender operations from JSON configuration files.")
    parser.add_argument(
        "--config",
        action="append",
        help="Path to a JSON configuration file. Can be specified multiple times."
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    if args.config:
        config_files = [Path(config) for config in args.config]
    else:
        config_files = CONFIG_FILES
    print("=" * 60)
    print("Blender Operation Runner")
    print("=" * 60)
    print(f"Project directory: {PROJECT_DIR}")
    print(f"Operations directory: {OPERATIONS_DIR}")
    print(f"Blender version: {bpy.app.version_string}")
    print(f"Config files: {len(config_files)}")
    print("=" * 60)
    for index, config_file in enumerate(config_files, start=1):
        print("\n" + "=" * 60)
        print(f"CONFIG {index}/{len(config_files)}")
        print(f"Running: {config_file}")
        print("=" * 60)
        success = run_operations_from_config(config_file)
        if not success:
            print(f"Config failed: {config_file}")
        else:
            print(f"Config completed: {config_file}")
    print("\n" + "=" * 60)
    print("All config files processed.")
    print("=" * 60)