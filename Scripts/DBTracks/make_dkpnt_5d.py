import re
import os
import trackshapeutils as tsu

if __name__ == "__main__":
    shape_load_path = "../../../../Content/PGA DK24/GLOBAL/SHAPES"
    shape_processed_path = "./Processed/DKPnt5d"
    ffeditc_path = "./ffeditc_unicode.exe"
    match_shapes = ["DB*Pnt5d*.s"]
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
        
        lod_dlevels = new_sfile.get_lod_dlevels()
        db_wm1c = new_sfile.get_prim_state_by_name("DB_WM1c")
        rails = new_sfile.get_prim_state_by_name("Rails")
        for lod_dlevel in lod_dlevels:
            db_wm1c_vertices = new_sfile.get_vertices_by_prim_state(lod_dlevel, db_wm1c)
            rails_vertices = new_sfile.get_vertices_by_prim_state(lod_dlevel, rails)
        
            for db_wm1c_vertex in db_wm1c_vertices:
                db_wm1c_vertex.point.y = "0.05" # Set height below trackbed to hide DB_WM1c
                new_sfile.update_vertex(db_wm1c_vertex)
            
            for rails_vertex in rails_vertices:
                if 'rgt' in sfile_name.lower():
                    if rails_vertex.point.x == 1.88105: # Right end of rod attached to DB_WM1c
                        rails_vertex.point.x = "0.75" # Set x equal to right rail position
                        new_sfile.update_vertex(rails_vertex)

                    if 1.02 <= rails_vertex.point.x <= 1.33 and rails_vertex.point.z <= 25: # Sleeper attachments that were connected to DB_WM1c
                        rails_vertex.point.y # Set height below trackbed to hide the sleeper attachments
                        new_sfile.update_vertex(rails_vertex)
                
                elif 'lft' in sfile_name.lower():
                    if rails_vertex.point.x == -1.88105: # Left end of rod attached to DB_WM1c
                        rails_vertex.point.x = "-0.75" # Set x equal to left rail position
                        new_sfile.update_vertex(rails_vertex)
                    
                    if -1.33 <= rails_vertex.point.x <= -1.02 and rails_vertex.point.z <= 25: # Sleeper attachments that were connected to DB_WM1c
                        rails_vertex.point.y = "0.05" # Set height below trackbed to hide the sleeper attachments
                        new_sfile.update_vertex(rails_vertex)

        new_sfile.save()
        new_sfile.compress(ffeditc_path)

        # Process .sd file
        sdfile_name = sfile_name.replace(".s", ".sd")
        new_sdfile_name = new_sfile_name.replace(".s", ".sd")

        sdfile = tsu.load_file(sdfile_name, shape_load_path)
        new_sdfile = sdfile.copy(new_filename=new_sdfile_name, new_directory=shape_processed_path)
        new_sdfile.replace_ignorecase(sfile_name, new_sfile_name)
        new_sdfile.save()

