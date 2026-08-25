import subprocess
import os
import sys

# Get the directory of the current script to find the GIMP script
_script_dir = os.path.dirname(os.path.abspath(__file__))

def process_image_gimp_operation(params):
    """
    Executes a GIMP script to process an image, e.g., change text layers.
    This function assumes GIMP is installed and its executable is in the system PATH,
    or a full path is provided in gimp_executable_path.

    Parameters:
        params (dict): A dictionary containing:
            'input_path' (str): Path to the input image file (e.g., XCF).
            'output_path' (str): Path to save the processed image.
            'text_layer_name' (str): The name of the text layer to modify.
            'new_text' (str): The new text to set for the layer.
            'gimp_script_name' (str): The name of the GIMP Python script to execute.
                                      This script should be in the 'gimp_scripts' subdirectory.
            'gimp_executable_path' (str, optional): Full path to the GIMP executable.
                                                    Defaults to "gimp" (assumes in PATH).
    """
    input_path = os.path.join(_script_dir, params['input_path'])
    output_path = os.path.join(_script_dir, params['output_path'])
    text_layer_name = params['text_layer_name']
    new_text = params['new_text']
    gimp_script_name = params['gimp_script_name']
    gimp_executable = params.get('gimp_executable_path', 'gimp')

    gimp_script_path = os.path.join(_script_dir, 'gimp_scripts', gimp_script_name)

    if not os.path.exists(gimp_script_path):
        print(f"Error: GIMP script not found at {gimp_script_path}", file=sys.stderr)
        return

    # Construct the GIMP batch command
    # -i: Run in non-interactive mode
    # -b: Execute a batch command/script.
    # The batch command calls the GIMP Python-fu script.
    # It must be wrapped in quotes for shell execution.
    gimp_command = [
        gimp_executable,
        '-i',
        '-b',
        f'(python-fu-change-text-layer RUN-NONINTERACTIVE "{input_path}" "{output_path}" "{text_layer_name}" "{new_text}")',
        '-b',
        '(gimp-quit 0)' # Quit GIMP after script execution
    ]

    print(f"Running GIMP command: {' '.join(gimp_command)}")

    try:
        # Use shell=True for complex commands with quotes and script-fu calls
        # Be careful with user-controlled input if shell=True is used
        result = subprocess.run(gimp_command, capture_output=True, text=True, check=True, shell=False)
        print("GIMP output:")
        print(result.stdout)
        if result.stderr:
            print("GIMP errors:")
            print(result.stderr, file=sys.stderr)
        print(f"Successfully processed image '{input_path}' with GIMP to '{output_path}'")
    except subprocess.CalledProcessError as e:
        print(f"GIMP command failed with error code {e.returncode}:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
    except FileNotFoundError:
        print(f"Error: GIMP executable '{gimp_executable}' not found.", file=sys.stderr)
        print("Please ensure GIMP is installed and its path is correctly set.", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

    print(f"Operation '{params['name']}' completed.")
