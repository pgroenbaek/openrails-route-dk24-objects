import os
import fnmatch
import subprocess
import shutil
import re


def find_trackshape_names(shape_path, match_shapes, ignore_shapes):
    """
    Find and return a list of track shape file names in the specified directory 
    that match a given pattern while excluding those that match the ignore list.

    Parameters:
        shape_path (str): Path to the directory containing shape files.
        match_shapes (str): Pattern to match shape files.
        ignore_shapes (list): List of patterns to ignore.

    Returns:
        list: List of shape file names that match the criteria.
    """
    track_shapes = []
    for file_name in os.listdir(shape_path):
        if fnmatch.fnmatch(file_name, match_shapes):
            if any([fnmatch.fnmatch(file_name, x) for x in ignore_shapes]):
                continue
            track_shapes.append(file_name)
    return track_shapes


def ensure_directory_exists(path):
    """
    Ensure that a given directory exists, creating it if necessary.

    Parameters:
        path (str): Path of the directory to check or create.
    """
    if not os.path.exists(path):
        os.makedirs(path)


def read_file(file_path, encoding='utf-16'):
    """
    Read and return the content of a file with the specified encoding.

    Parameters:
        file_path (str): Path to the file to read.
        encoding (str, optional): File encoding (default is 'utf-16').

    Returns:
        str: Content of the file.
    """
    with open(file_path, 'r', encoding=encoding) as f:
        return f.read()


def write_file(file_path, text, encoding='utf-16'):
    """
    Write the given text to a file with the specified encoding.

    Parameters:
        file_path (str): Path to the file to write.
        text (str): Text to write into the file.
        encoding (str, optional): File encoding (default is 'utf-16').
    """
    with open(file_path, 'w', encoding=encoding) as f:
        f.write(text)


def is_binary_string(bytes):
    """
    Determine if a given byte sequence represents binary data.

    Parameters:
        bytes (bytes): Byte sequence to check.

    Returns:
        bool: True if the data is binary, False otherwise.
    """
    textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
    return bool(bytes.translate(None, textchars))


def compress_shape(ffeditc_path, shape_file):
    """
    Compress a shape file using ffeditc if it is not already binary.

    Parameters:
        ffeditc_path (str): Path to the ffeditc executable.
        shape_file (str): Path to the shape file to compress.
    """
    if not is_binary_string(open(shape_file, 'rb').read(256)):
        subprocess.call([ffeditc_path, shape_file, "/o:" + shape_file])


def decompress_shape(ffeditc_path, shape_file):
    """
    Decompress a shape file using ffeditc if it is in binary format.

    Parameters:
        ffeditc_path (str): Path to the ffeditc executable.
        shape_file (str): Path to the shape file to decompress.
    """
    if is_binary_string(open(shape_file, 'rb').read(256)):
        subprocess.call([ffeditc_path, shape_file, "/u", "/o:" + shape_file])


def replace_ignorecase(text, search_exp, replace_exp):
    """
    Replace occurrences of a pattern in a given text, ignoring case.

    Parameters:
        text (str): The original text.
        search_exp (str): The regular expression pattern to search for.
        replace_exp (str): The replacement string.

    Returns:
        str: The modified text with replacements applied.
    """
    pattern = re.compile(search_exp, re.IGNORECASE)
    return pattern.sub(replace_exp, text)



if __name__ == "__main__":
    shape_load_path = "..\\..\\..\\..\\Content\\PGA DK24\\GLOBAL\\SHAPES"
    shape_converted_path = ".\\Converted_from_DB2s_to_DB2fb"
    ffeditc_path = ".\\ffeditc_unicode.exe"
    match_shapes = "DB2s_*.s"
    ignore_shapes = ["*Tun*", "*Pnt*", "*Frog*"]
    
    trackshape_names = find_trackshape_names(shape_load_path, match_shapes, ignore_shapes)

    ensure_directory_exists(shape_converted_path)

    for original_shape_name in trackshape_names:
        print("File %d of %d..." % (trackshape_names.index(original_shape_name), len(trackshape_names)))
        
        original_shape_sdname = original_shape_name.replace(".s", ".sd")
        converted_shape_name = original_shape_name.replace("DB2s_", "DB2fb_")
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
                sfile_lines[line_idx] = replace_ignorecase(sfile_lines[line_idx], "DB_TrackSfs2.ace", "DB_Track2.ace")
                sfile_lines[line_idx] = replace_ignorecase(sfile_lines[line_idx], "DB_TrackSfs2s.ace", "DB_Track2s.ace")
                sfile_lines[line_idx] = replace_ignorecase(sfile_lines[line_idx], "DB_TrackSfs2w.ace", "DB_Track2w.ace")
                sfile_lines[line_idx] = replace_ignorecase(sfile_lines[line_idx], "DB_TrackSfs2sw.ace", "DB_Track2sw.ace")
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