import os
import trackshapeutils as tsu

if __name__ == "__main__":
    shape_load_path = "../../../../Content/PGA DK24/GLOBAL/SHAPES"
    shape_processed_path = "./Processed/DB22f"
    ffeditc_path = "./ffeditc_unicode.exe"
    match_shapes = ["DB2f_*.s"]
    ignore_shapes = ["*Tun*", "*Pnt*", "*Frog*"]
    
    os.makedirs(shape_processed_path, exist_ok=True)

    shape_names = tsu.find_directory_files(shape_load_path, match_shapes, ignore_shapes)

    for idx, sfile_name in enumerate(shape_names):
        print(f"Shape {idx} of {len(shape_names)}...")
        
        # Convert .s file
        new_sfile_name = sfile_name.replace("DB2f_", "DB22f_")

        sfile = tsu.load_shape(sfile_name, shape_load_path)
        new_sfile = sfile.copy(new_filename=new_sfile_name, new_directory=shape_processed_path)
        new_sfile.decompress(ffeditc_path)

        new_sfile.replace_ignorecase("DB_Track2.ace", "DB_Track22.ace")
        new_sfile.replace_ignorecase("DB_Track2s.ace", "DB_Track22s.ace")
        new_sfile.replace_ignorecase("DB_Track2w.ace", "DB_Track22w.ace")
        new_sfile.replace_ignorecase("DB_Track2sw.ace", "DB_Track22sw.ace")

        new_sfile.save()
        new_sfile.compress(ffeditc_path)

        # Convert .sd file
        sdfile_name = sfile_name.replace(".s", ".sd")
        new_sdfile_name = new_sfile_name.replace(".s", ".sd")

        sdfile = tsu.load_file(sdfile_name, shape_load_path)
        new_sdfile = sdfile.copy(new_filename=new_sdfile_name, new_directory=shape_processed_path)
        new_sdfile.replace_ignorecase(sfile_name, new_sfile_name)
        new_sdfile.save()
