import trackshapeutils as tsu
import shutil


if __name__ == "__main__":
    shape_load_path = "..\\..\\..\\..\\Content\\PGA DK24\\GLOBAL\\SHAPES"
    shape_converted_path = ".\\Converted_from_DB1s_to_DB1fb"
    ffeditc_path = ".\\ffeditc_unicode.exe"
    match_shapes = "DB1s_*.s"
    ignore_shapes = ["*Tun*", "*Pnt*", "*Frog*"]
    
    trackshape_names = tsu.find_trackshape_names(shape_load_path, match_shapes, ignore_shapes)

    tsu.ensure_directory_exists(shape_converted_path)

    for original_shape_name in trackshape_names:
        print("File %d of %d..." % (trackshape_names.index(original_shape_name), len(trackshape_names)))
        
        original_shape_sdname = original_shape_name.replace(".s", ".sd")
        converted_shape_name = original_shape_name.replace("DB1s_", "DB1fb_")
        converted_shape_sdname = converted_shape_name.replace(".s", ".sd")
        original_sfile = "%s\\%s" % (shape_load_path, original_shape_name)
        original_sdfile = "%s\\%s" % (shape_load_path, original_shape_sdname)
        converted_sfile = "%s\\%s" % (shape_converted_path, converted_shape_name)
        converted_sdfile = "%s\\%s" % (shape_converted_path, converted_shape_sdname)

        shutil.copyfile(original_sfile, converted_sfile)
        shutil.copyfile(original_sdfile, converted_sdfile)

        tsu.decompress_shape(ffeditc_path, converted_sfile)

        sfile_text = tsu.read_file(converted_sfile)
        sfile_lines = sfile_text.split("\n")
        for line_idx in range(0, len(sfile_lines)):
            sfile_line = sfile_lines[line_idx]
            if ".ace" in sfile_line.lower():
                sfile_lines[line_idx] = tsu.replace_ignorecase(sfile_lines[line_idx], "DB_TrackSfs1.ace", "DB_Track1.ace")
                sfile_lines[line_idx] = tsu.replace_ignorecase(sfile_lines[line_idx], "DB_TrackSfs1s.ace", "DB_Track1s.ace")
                sfile_lines[line_idx] = tsu.replace_ignorecase(sfile_lines[line_idx], "DB_TrackSfs1w.ace", "DB_Track1w.ace")
                sfile_lines[line_idx] = tsu.replace_ignorecase(sfile_lines[line_idx], "DB_TrackSfs1sw.ace", "DB_Track1sw.ace")
            elif "point (" in sfile_line.lower():
                parts = sfile_line.split(" ")
                if parts[3] == "0.133":
                    parts[3] = "0.0833"
                elif parts[3] == "0.145":
                    parts[3] = "0.0945"
                sfile_lines[line_idx] = " ".join(parts)
        sfile_text = "\n".join(sfile_lines)
        tsu.write_file(converted_sfile, sfile_text)

        tsu.compress_shape(ffeditc_path, converted_sfile)

        sdfile_text = tsu.read_file(converted_sdfile)
        sdfile_text = tsu.replace_ignorecase(sdfile_text, original_shape_name, converted_shape_name)
        tsu.write_file(converted_sdfile, sdfile_text)