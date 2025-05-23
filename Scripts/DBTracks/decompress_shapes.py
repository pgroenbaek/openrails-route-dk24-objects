import os
import trackshapeutils as tsu

if __name__ == "__main__":
    shape_load_path = "../../../../Content/PGA DK24/GLOBAL/SHAPES"
    #shape_load_path = "../../../../Content/PGA DK24/ROUTES/OR_DK24/SHAPES"
    ffeditc_path = "./ffeditc_unicode.exe"
    match_files = ["*.s"]
    ignore_files = ["*.sd"]

    shape_names = tsu.find_directory_files(shape_load_path, match_files, ignore_files)

    for idx, sfile_name in enumerate(shape_names):
        print(f"Shape {idx + 1} of {len(shape_names)}...")

        sfile = tsu.load_shape(sfile_name, shape_load_path)
        sfile.decompress(ffeditc_path)