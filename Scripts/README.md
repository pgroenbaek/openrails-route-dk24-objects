


## Running the Blender scripts

### Prerequisites

- Blender 4.2+

### Usage

Paste the scripts into the Blender scripting console.


## Running the GIMP scripts

### Prerequisites

- GIMP ~2.0

### Usage

Paste the scripts into the GIMP Python scripting console.


## Running the scripts to create edited shapes and textures

### Prerequisites

- Python 3.7+
- The DK24 route shapes/textures folders

### Set up a virtual env

Create a virtual env. You only need to do this once.

```bash
python -m venv dk24-objects
```

To activate the virtual env:
- Linux / macOS: `source dk24-objects/bin/activate`
- Windows (powershell): `dk24-objects\Scripts\Activate.ps1`
- Windows (cmd): `dk24-objects\Scripts\activate.bat`

### Install dependencies

Install the dependencies using `pip`:

```bash
pip install -r requirements.txt
```

### Configure paths

Configure the `scripts/config.ini` file with the appropriate paths to the utility programs, the DBTracks zip-file packages, and to the input/output-folder.

For example:
```ini
[utilities]
ffeditc_path = C:/path/to/ffeditc_unicode.exe
ace2png_path = C:/path/to/ace2png.exe
aceit_path = C:/path/to/aceit.exe

[dk24]
route_path = C:/path/to/route

[shapes]
output_path = ../Shapes

[textures]
output_path = ../Textures
```

### Run the scripts to create edited shapes

Now you can run each `.py` script to generate the modified shapes. Run the commands from the scripts directory.

For example:

```bash
python ./scripts/somefolder/somescript.py
```

You can also run all scripts at once:

```bash
python ./scripts/run_all.py
```

## License

The scripts are licensed under [GNU GPL v3](/LICENSE).

All shapes and textures referenced in the scripts are the original work of their respective authors, and all rights to them belong to those authors.



