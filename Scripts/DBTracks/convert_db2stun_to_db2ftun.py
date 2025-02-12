import os
import fnmatch
import subprocess
import shutil
import re


def find_trackshape_names(shape_path, match_shapes, ignore_shapes):
    track_shapes = []
    for file_name in os.listdir(shape_path):
        if fnmatch.fnmatch(file_name, match_shapes):
            if any([fnmatch.fnmatch(file_name, x) for x in ignore_shapes]):
                continue
            track_shapes.append(file_name)
    return track_shapes


def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)


def read_file(file_path, encoding='utf-16'):
    with open(file_path, 'r', encoding=encoding) as f:
        return f.read()


def write_file(file_path, text, encoding='utf-16'):
    with open(file_path, 'w', encoding=encoding) as f:
        f.write(text)


def is_binary_string(bytes):
    textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
    return bool(bytes.translate(None, textchars))


def compress_shape(ffeditc_path, shape_file):
    if not is_binary_string(open(shape_file, 'rb').read(256)):
        subprocess.call([ffeditc_path, shape_file, "/o:" + shape_file])


def decompress_shape(ffeditc_path, shape_file):
    if is_binary_string(open(shape_file, 'rb').read(256)):
        subprocess.call([ffeditc_path, shape_file, "/u", "/o:" + shape_file])


def replace_ignorecase(text, search_exp, replace_exp):
    pattern = re.compile(search_exp, re.IGNORECASE)
    return pattern.sub(replace_exp, text)



if __name__ == "__main__":
    shape_load_path = "..\\..\\..\\..\\Content\\PGA DK24\\GLOBAL\\SHAPES"
    shape_converted_path = ".\\Converted_from_DB2sTun_to_DB2ft"
    ffeditc_path = ".\\ffeditc_unicode.exe"
    match_shapes = "DB2s_*Tun*.s"
    ignore_shapes = ["*Pnt*", "*Frog*"]
    
    trackshape_names = find_trackshape_names(shape_load_path, match_shapes, ignore_shapes)

    ensure_directory_exists(shape_converted_path)

    for original_shape_name in trackshape_names:
        print("File %d of %d..." % (trackshape_names.index(original_shape_name), len(trackshape_names)))
        
        original_shape_sdname = original_shape_name.replace(".s", ".sd")
        converted_shape_name = original_shape_name.replace("DB2s_", "DB2ft_")
        converted_shape_sdname = converted_shape_name.replace(".s", ".sd")
        original_sfile = "%s\\%s" % (shape_load_path, original_shape_name)
        original_sdfile = "%s\\%s" % (shape_load_path, original_shape_sdname)
        converted_sfile = "%s\\%s" % (shape_converted_path, converted_shape_name)
        converted_sdfile = "%s\\%s" % (shape_converted_path, converted_shape_sdname)

        shutil.copyfile(original_sfile, converted_sfile)
        shutil.copyfile(original_sdfile, converted_sdfile)

        decompress_shape(ffeditc_path, converted_sfile)

        sfile_text = read_file(converted_sfile)
        sfile_lines = sfile_text.split("\n")
        for line_idx in range(0, len(sfile_lines)):
            sfile_line = sfile_lines[line_idx]
            if ".ace" in sfile_line.lower():
                sfile_lines[line_idx] = replace_ignorecase(sfile_lines[line_idx], "DB_TunTrackSfs2.ace", "DB_TunTrack2.ace")
                sfile_lines[line_idx] = replace_ignorecase(sfile_lines[line_idx], "DB_TunTrackSfs2s.ace", "DB_TunTrack2s.ace")
                sfile_lines[line_idx] = replace_ignorecase(sfile_lines[line_idx], "DB_TunTrackSfs2w.ace", "DB_TunTrack2w.ace")
                sfile_lines[line_idx] = replace_ignorecase(sfile_lines[line_idx], "DB_TunTrackSfs2sw.ace", "DB_TunTrack2sw.ace")
            elif "point (" in sfile_line.lower():
                tokens = sfile_line.split(" ")
                if tokens[3] == "0.133":
                    tokens[3] = "0.0833"
                elif tokens[3] == "0.145":
                    tokens[3] = "0.0945"
                sfile_lines[line_idx] = " ".join(tokens)
        sfile_text = "\n".join(sfile_lines)
        write_file(converted_sfile, sfile_text)

        compress_shape(ffeditc_path, converted_sfile)

        sdfile_text = read_file(converted_sdfile)
        sdfile_text = replace_ignorecase(sdfile_text, original_shape_name, converted_shape_name)
        write_file(converted_sdfile, sdfile_text)