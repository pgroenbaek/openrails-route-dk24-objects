import re
import os
import trackshapeutils as tsu

if __name__ == "__main__":
    shape_load_path = "../../../../Content/PGA DK24/GLOBAL/SHAPES"
    shape_processed_path = "./Processed/NRWire"
    ffeditc_path = "./ffeditc_unicode.exe"
    match_shapes = ["DB2f_A1t*Strt*.s"]
    ignore_shapes = ["*Tun*", "*Pnt*", "*Wtr*", "*.sd"]
    
    os.makedirs(shape_processed_path, exist_ok=True)

    shape_names = tsu.find_directory_files(shape_load_path, match_shapes, ignore_shapes)

    for idx, sfile_name in enumerate(shape_names):
        print(f"Shape {idx} of {len(shape_names)}...")

        # Process .s file
        new_sfile_name = sfile_name.replace("DB2f_A1t", "NR_Wire_")
        new_sfile_name = new_sfile_name.replace("DB2f_a1t", "NR_Wire_")

        sfile = tsu.load_shape(sfile_name, shape_load_path)
        new_sfile = sfile.copy(new_filename=new_sfile_name, new_directory=shape_processed_path)
        new_sfile.decompress(ffeditc_path)

        mt_cwire_prim_states = new_sfile.get_prim_states_by_name("mt_cwire")
        mt_cwire_prim_state_idxs = [x.idx for x in mt_cwire_prim_states]
        lod_dlevels = new_sfile.get_lod_dlevels()

        for lod_dlevel in lod_dlevels:
            subobject_idxs = new_sfile.get_subobject_idxs_in_lod_dlevel(lod_dlevel)

            for subobject_idx in subobject_idxs:
                indexed_trilists = new_sfile.get_indexed_trilists_in_subobject(lod_dlevel, subobject_idx)

                # Remove all triangles not attached to the 'mt_cwire' prim state.
                for prim_state_idx in indexed_trilists:
                    if prim_state_idx not in mt_cwire_prim_state_idxs:
                        for indexed_trilist in indexed_trilists[prim_state_idx]:
                            indexed_trilist.vertex_idxs = []
                            indexed_trilist.normal_idxs = []
                            indexed_trilist.flags = []
                            new_sfile.update_indexed_trilist(indexed_trilist)

        new_sfile.save()
        new_sfile.compress(ffeditc_path)

        # Process .sd file
        sdfile_name = sfile_name.replace(".s", ".sd")
        new_sdfile_name = new_sfile_name.replace(".s", ".sd")

        sdfile = tsu.load_file(sdfile_name, shape_load_path)
        new_sdfile = sdfile.copy(new_filename=new_sdfile_name, new_directory=shape_processed_path)
        new_sdfile.replace_ignorecase(sfile_name, new_sfile_name)
        new_sdfile.save()