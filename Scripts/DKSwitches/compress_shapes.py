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

import os
import trackshapeutils as tsu

if __name__ == "__main__":
    #shape_load_path = "../../../../Content/PGA DK24/GLOBAL/SHAPES"
    shape_load_path = "../../../../Content/PGA DK24/ROUTES/OR_DK24/SHAPES"
    ffeditc_path = "./ffeditc_unicode.exe"
    match_files = ["PGA_DKGantry*.s"]
    ignore_files = ["*.sd"]

    shape_names = tsu.find_directory_files(shape_load_path, match_files, ignore_files)

    for idx, sfile_name in enumerate(shape_names):
        print(f"Shape {idx + 1} of {len(shape_names)}...")

        sfile = tsu.load_shape(sfile_name, shape_load_path)
        sfile.compress(ffeditc_path)