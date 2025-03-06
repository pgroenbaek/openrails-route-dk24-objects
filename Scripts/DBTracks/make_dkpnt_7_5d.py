import trackshapeutils as tsu
import shutil
import re
import numpy as np


if __name__ == "__main__":
    shape_load_path = "..\\..\\..\\..\\Content\\PGA DK24\\GLOBAL\\SHAPES"
    shape_converted_path = ".\\DK_Switches"
    ffeditc_path = ".\\ffeditc_unicode.exe"
    match_shapes = "DB*Pnt7_5d*.s"
    ignore_shapes = ["*Tun*", "*EndPnt*", "*Frog*"]
    
    trackshape_names = tsu.find_trackshape_names(shape_load_path, match_shapes, ignore_shapes)

    tsu.ensure_directory_exists(shape_converted_path)

    for original_shape_name in trackshape_names:
        print("File %d of %d..." % (trackshape_names.index(original_shape_name), len(trackshape_names)))

        original_shape_sdname = original_shape_name.replace(".s", ".sd")
        converted_shape_name = original_shape_name.replace("DB", "DK")
        converted_shape_sdname = converted_shape_name.replace(".s", ".sd")
        original_sfile = "%s\\%s" % (shape_load_path, original_shape_name)
        original_sdfile = "%s\\%s" % (shape_load_path, original_shape_sdname)
        converted_sfile = "%s\\%s" % (shape_converted_path, converted_shape_name)
        converted_sdfile = "%s\\%s" % (shape_converted_path, converted_shape_sdname)

        shutil.copyfile(original_sfile, converted_sfile)
        shutil.copyfile(original_sdfile, converted_sdfile)

        tsu.decompress_shape(ffeditc_path, converted_sfile)

        sfile_text = tsu.read_file(converted_sfile)
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_WL1a.ace", "DK_WL1a.ace")
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_WL3a.ace", "DK_WL3a.ace")
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_WM1m.ace", "DK_WM1m.ace")
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_WM2m.ace", "DK_WM2m.ace")
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_WM3b.ace", "DK_WM3b.ace")
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_WM11m.ace", "DK_WM11m.ace")
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_WM20m.ace", "DK_WM20m.ace")
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_WM21m.ace", "DK_WM21m.ace")
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_WS3a.ace", "DK_WS3a.ace")
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_WS4a.ace", "DK_WS4a.ace")
        tsu.write_file(converted_sfile, sfile_text)

        tsu.compress_shape(ffeditc_path, converted_sfile)

        sdfile_text = tsu.read_file(converted_sdfile)
        sdfile_text = tsu.replace_ignorecase(sdfile_text, original_shape_name, converted_shape_name)
        tsu.write_file(converted_sdfile, sdfile_text)