import re
import os
import trackshapeutils as tsu

# Polyline ( Name ( "mb_embankment_left" ) DeltaTexCoord ( 0.2 0 )
# 	Vertex ( Position ( -3.4000 0.0200 ) Normal ( 0 1 0 ) TexCoord ( 0.0 0.7300 ) PositionControl ( "None" ) )
# 	Vertex ( Position ( -2.4500 0.0200 ) Normal ( 0 1 0 ) TexCoord ( 0.0 0.8880 ) PositionControl ( "None" ) )
# 	Vertex ( Position ( -2.1000 -0.1600 ) Normal ( 0 1 0 ) TexCoord ( 0.0 0.9180 ) PositionControl ( "Outside" ) )
# )
# Polyline ( Name ( "mb_embankment_right" ) DeltaTexCoord ( 0.2 0 )
# 	Vertex ( Position ( 2.1000 -0.1600 ) Normal ( 0 1 0 ) TexCoord ( 0.0 0.9180 ) PositionControl ( "Outside" ) )
# 	Vertex ( Position ( 2.4500 0.0200 ) Normal ( 0 1 0 ) TexCoord ( 0.0 0.8880 ) PositionControl ( "None" ) )
# 	Vertex ( Position ( 3.4000 0.0200 ) Normal ( 0 1 0 ) TexCoord ( 0.0 0.7300 ) PositionControl ( "None" ) )

if __name__ == "__main__":
    shape_load_path = "../../../../Content/PGA DK24/GLOBAL/SHAPES"
    shape_processed_path = "./Processed/DB22Emb"
    ffeditc_path = "./ffeditc_unicode.exe"
    match_shapes = ["DB22f_A1tPnt7_5dRgt.s"]#"DB22f_*Pnt*", "DB22f_*Frog*", "DB22f_*Xover*"]
    ignore_shapes = ["*EndPnt*", "*.sd"]
    
    os.makedirs(shape_processed_path, exist_ok=True)

    shape_names = tsu.find_directory_files(shape_load_path, match_shapes, ignore_shapes)

    for idx, sfile_name in enumerate(shape_names):
        print(f"Shape {idx} of {len(shape_names)}...")

        # Process .s file
        new_sfile_name = sfile_name.replace("DB22f_", "DB22fb_")
        new_sfile_name = new_sfile_name.replace("DB22_", "DB22b_")

        sfile = tsu.load_shape(sfile_name, shape_load_path)
        new_sfile = sfile.copy(new_filename=new_sfile_name, new_directory=shape_processed_path)
        new_sfile.decompress(ffeditc_path)

        tsection_sfile_name = sfile_name.replace("DB22f_", "")
        tsection_sfile_name = tsection_sfile_name.replace("DB22_", "")
        trackcenters = tsu.generate_trackcenters_from_global_tsection(shape_name=tsection_sfile_name, num_points_per_meter=12)
        
        update_vertex_data = [] # Format: [(vertex, new_height, new_center_distance, new_u_value, new_v_value, new_normal_vecx, new_normal_vecy, new_normal_vecz), ...]
        new_triangles = [] # Format: [(vertex1, vertex2, vertex3), ...]
        prev_vertices = None

        lod_dlevels = [200, 500]
        mb_track2sw = new_sfile.get_prim_states_by_name("MB_Track2sw")
        rails = new_sfile.get_prim_states_by_name("Rails")[0]
        for lod_dlevel in lod_dlevels:
            mb_track2sw_vertices = new_sfile.get_vertices_by_prim_state(lod_dlevel, mb_track2sw[0])

            for mb_track2sw_vertex in mb_track2sw_vertices:
                closest_trackcenter = tsu.find_closest_trackcenter(mb_track2sw_vertex.point, trackcenters, plane="xz")
                closest_centerpoint = tsu.find_closest_centerpoint(mb_track2sw_vertex.point, closest_trackcenter, plane="xz")
                distance_from_center = tsu.signed_distance_between(mb_track2sw_vertex.point, closest_centerpoint, plane="xz")
                
                if mb_track2sw_vertex.uv_point.u == 0.8620:
                    pass
                
                if mb_track2sw_vertex.uv_point.u == -0.1389:
                    pass
                
                # TODO actually make the embankments
        
        mt_trackbase = new_sfile.get_prim_states_by_name("mt_trackbase")
        mt_trackbase_vertices = new_sfile.get_vertices_by_prim_state(800, mt_trackbase[0])
        
        for mt_trackbase_vertex in mt_trackbase_vertices:
            if mt_trackbase_vertex.uv_point.u == 0.8620:
                pass
            
            if mt_trackbase_vertex.uv_point.u == -0.1389:
                pass
        
        print("")

        # Update the values of existing and created vertices.
        for idx, (vertex, new_height, new_center_distance, new_u_value, new_v_value, new_normal_vecx, new_normal_vecy, new_normal_vecz) in enumerate(update_vertex_data):
            print(f"\tUpdating vertex {idx + 1} of {len(update_vertex_data)}", end='\r')
            closest_trackcenter = tsu.find_closest_trackcenter(vertex.point, trackcenters, plane="xz")
            new_position = tsu.get_new_position_from_trackcenter(new_center_distance, vertex.point, closest_trackcenter)
            vertex.point.x = new_position.x
            vertex.point.y = new_height
            vertex.point.z = new_position.z
            vertex.uv_point.u = new_u_value
            vertex.uv_point.v = new_v_value
            vertex.normal.vec_x = new_normal_vecx
            vertex.normal.vec_y = new_normal_vecy
            vertex.normal.vec_z = new_normal_vecz
            new_sfile.update_vertex(vertex)
        
        print("")

        # Insert new triangles between the created vertices.
        for idx, (vertex1, vertex2, vertex3) in enumerate(new_triangles):
            print(f"\tInserting triangle {idx + 1} of {len(new_triangles)}", end='\r')
            new_sfile.insert_triangle_between(railside_indexed_trilist, vertex1, vertex2, vertex3)

        print("")

        new_sfile.save()
        #new_sfile.compress(ffeditc_path)

        # Process .sd file
        sdfile_name = sfile_name.replace(".s", ".sd")
        new_sdfile_name = new_sfile_name.replace(".s", ".sd")

        sdfile = tsu.load_file(sdfile_name, shape_load_path)
        new_sdfile = sdfile.copy(new_filename=new_sdfile_name, new_directory=shape_processed_path)
        new_sdfile.replace_ignorecase(sfile_name, new_sfile_name)
        new_sdfile.save()

