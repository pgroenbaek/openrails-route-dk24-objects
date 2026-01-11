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

import re
import os
import trackshapeutils as tsu

if __name__ == "__main__":
    shape_load_path = "../../../../Content/PGA DK24/GLOBAL/SHAPES"
    shape_processed_path = "./Processed/DKPnt7_5d"
    ffeditc_path = "./ffeditc_unicode.exe"
    match_shapes = ["DB*Pnt7_5d*.s"]
    ignore_shapes = ["*Tun*", "*EndPnt*", "*Frog*", "DB1s_*", "DB1z_*", "DB2s_*", "DB2z_*", "DB20z_*"]
    
    os.makedirs(shape_processed_path, exist_ok=True)

    shape_names = tsu.find_directory_files(shape_load_path, match_shapes, ignore_shapes)

    for idx, sfile_name in enumerate(shape_names):
        print(f"Shape {idx} of {len(shape_names)}...")

        # Process .s file
        new_sfile_name = sfile_name.replace("DB", "DK")

        sfile = tsu.load_shape(sfile_name, shape_load_path)
        new_sfile = sfile.copy(new_filename=new_sfile_name, new_directory=shape_processed_path)
        new_sfile.decompress(ffeditc_path)

        new_sfile.replace_ignorecase("DB_WL1a.ace", "DK_WL1a.ace")
        new_sfile.replace_ignorecase("DB_WL3a.ace", "DK_WL3a.ace")
        new_sfile.replace_ignorecase("DB_WM1m.ace", "DK_WM1m.ace")
        new_sfile.replace_ignorecase("DB_WM2m.ace", "DK_WM2m.ace")
        new_sfile.replace_ignorecase("DB_WM3b.ace", "DK_WM3b.ace")
        new_sfile.replace_ignorecase("DB_WM11m.ace", "DK_WM11m.ace")
        new_sfile.replace_ignorecase("DB_WM20m.ace", "DK_WM20m.ace")
        new_sfile.replace_ignorecase("DB_WM21m.ace", "DK_WM21m.ace")
        new_sfile.replace_ignorecase("DB_WS3a.ace", "DK_WS3a.ace")
        new_sfile.replace_ignorecase("DB_WS4a.ace", "DK_WS4a.ace")
        
        new_sfile.save()
        new_sfile.compress(ffeditc_path)

        # Process .sd file
        sdfile_name = sfile_name.replace(".s", ".sd")
        new_sdfile_name = new_sfile_name.replace(".s", ".sd")

        sdfile = tsu.load_file(sdfile_name, shape_load_path)
        new_sdfile = sdfile.copy(new_filename=new_sdfile_name, new_directory=shape_processed_path)
        new_sdfile.replace_ignorecase(sfile_name, new_sfile_name)
        new_sdfile.save()