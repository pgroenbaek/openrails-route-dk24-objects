import os
import trackshapeutils as tsu

if __name__ == "__main__":
    shape_load_path = "../../../../Content/PGA DK24/GLOBAL/SHAPES"
    shape_processed_path = "./Processed/DB1ft"
    ffeditc_path = "./ffeditc_unicode.exe"
    match_shapes = ["DB1s_*Tun*.s"]
    ignore_shapes = ["*Pnt*", "*Frog*"]
    
    os.makedirs(shape_processed_path, exist_ok=True)

    shape_names = tsu.find_directory_files(shape_load_path, match_shapes, ignore_shapes)

    for idx, sfile_name in enumerate(shape_names):
        print(f"Shape {idx} of {len(shape_names)}...")
        
        # Convert .s file
        new_sfile_name = sfile_name.replace("DB1s_", "DB1ft_")

        sfile = tsu.load_shape(sfile_name, shape_load_path)
        new_sfile = sfile.copy(new_filename=new_sfile_name, new_directory=shape_processed_path)
        new_sfile.decompress(ffeditc_path)

        new_sfile.replace_ignorecase("DB_TunTrackSfs1.ace", "DB_TunTrack1.ace")
        new_sfile.replace_ignorecase("DB_TunTrackSfs1s.ace", "DB_TunTrack1s.ace")
        new_sfile.replace_ignorecase("DB_TunTrackSfs1w.ace", "DB_TunTrack1w.ace")
        new_sfile.replace_ignorecase("DB_TunTrackSfs1sw.ace", "DB_TunTrack1sw.ace")

        lod_dlevel = 500
        subobject_idxs = new_sfile.get_subobject_idxs_in_lod_dlevel(lod_dlevel)
        for subobject_idx in subobject_idxs:
            vertices_in_subobject = new_sfile.get_vertices_in_subobject(lod_dlevel, subobject_idx)
            for vertex in vertices_in_subobject:
                if vertex.point.y == 0.133:
                    vertex.point.y = 0.0833
                    new_sfile.update_vertex(vertex)
                elif vertex.point.y == 0.145:
                    vertex.point.y = 0.0945
                    new_sfile.update_vertex(vertex)

        new_sfile.save()
        new_sfile.compress(ffeditc_path)

        # Convert .sd file
        sdfile_name = sfile_name.replace(".s", ".sd")
        new_sdfile_name = new_sfile_name.replace(".s", ".sd")

        sdfile = tsu.load_file(sdfile_name, shape_load_path)
        new_sdfile = sdfile.copy(new_filename=new_sdfile_name, new_directory=shape_processed_path)
        new_sdfile.replace_ignorecase(sfile_name, new_sfile_name)
        new_sdfile.save()
