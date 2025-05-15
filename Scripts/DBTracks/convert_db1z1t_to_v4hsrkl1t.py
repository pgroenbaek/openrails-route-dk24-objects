import re
import os
import trackshapeutils as tsu

if __name__ == "__main__":
    shape_load_path = "../../../../Content/PGA DK24/GLOBAL/SHAPES"
    shape_processed_path = "./Processed/V4hsRKL"
    ffeditc_path = "./ffeditc_unicode.exe"
    match_shapes = ["DB1z_a1t*.s"]
    ignore_shapes = ["*Tun*", "*Pnt*", "*Frog*"]
    
    os.makedirs(shape_processed_path, exist_ok=True)

    shape_names = tsu.find_directory_files(shape_load_path, match_shapes, ignore_shapes)

    for idx, sfile_name in enumerate(shape_names):
        print(f"Shape {idx} of {len(shape_names)}...")

        track_length = None
        curve_radius = None
        curve_angle = None
        trackcenter = None

        if "strt" in sfile_name.lower():
            match = re.search(r'a(\d+)t(\d+)([m])', sfile_name.lower())

            if match:
                track_length = int(match.group(2))

            if track_length is not None:
                trackcenter = tsu.generate_straight_centerpoints(length=track_length)
        else:
            match_radius = re.search(r'a(\d+)t(\d+)(r)', sfile_name.lower())
            match_angle = re.search(r'r(\d+)(d)', sfile_name.lower())

            if match_radius:
                curve_radius = int(match_radius.group(2))

            if match_angle:
                curve_angle = -int(match_angle.group(1))

            if curve_radius is not None and curve_angle is not None:
                trackcenter = tsu.generate_curve_centerpoints(curve_radius=curve_radius, curve_angle=curve_angle)
        
        if trackcenter is None:
            print(f"Unable to parse shape name '{sfile_name}', skipping...")
            continue

        # Process .s file
        new_sfile_name = sfile_name.replace("DB1z_", "V4hs1t_RKL_").replace("A1t", "").replace("a1t", "")

        sfile = tsu.load_shape(sfile_name, shape_load_path)
        new_sfile = sfile.copy(new_filename=new_sfile_name, new_directory=shape_processed_path)
        new_sfile.decompress(ffeditc_path)

        new_sfile.replace_ignorecase("DB_Rails1.ace", "V4_Rails1.ace")
        new_sfile.replace_ignorecase("DB_Rails1w.ace", "V4_Rails1.ace")
        new_sfile.replace_ignorecase("DB_Track1.ace", "V4_RKLb.ace")
        new_sfile.replace_ignorecase("DB_Track1s.ace", "V4_RKLs.ace")
        new_sfile.replace_ignorecase("DB_Track1w.ace", "V4_RKLb.ace")
        new_sfile.replace_ignorecase("DB_Track1sw.ace", "V4_RKLs.ace")
        new_sfile.replace_ignorecase("DB_TrackSfs1.ace", "V4_RKLb.ace")
        new_sfile.replace_ignorecase("DB_TrackSfs1s.ace", "V4_RKLs.ace")
        new_sfile.replace_ignorecase("DB_TrackSfs1w.ace", "V4_RKLb.ace")
        new_sfile.replace_ignorecase("DB_TrackSfs1sw.ace", "V4_RKLs.ace")

        # RKL side
        # [Vector((-1.4025001525878906, 0.0, -0.12800000607967377))]
        # [Vector((-1.4125001430511475, 0.0, -0.019999999552965164))]
        # [Vector((-2.43250036239624, 0.0, 0.009999999776482582))]

        # normal track side
        # [Vector((-1.2999999523162842, 0.0, -0.13499999046325684))]
        # [Vector((-1.7000000476837158, 0.0, -0.13589999079704285))]
        # [Vector((-2.5999999046325684, 0.0, 0.019999999552965164))]

        lod_dlevels = new_sfile.get_lod_dlevels()
        mb_sleeperbase = new_sfile.get_prim_state_by_name("mb_sleeperbase")
        mb_trackbed = new_sfile.get_prim_state_by_name("mb_trackbed")
        mt_trackbed = new_sfile.get_prim_state_by_name("mt_trackbed")

        for lod_dlevel in lod_dlevels:
            mb_sleeperbase_vertices = new_sfile.get_vertices_by_prim_state(lod_dlevel, mb_sleeperbase)
            mb_trackbed_vertices = new_sfile.get_vertices_by_prim_state(lod_dlevel, mb_trackbed)
            mt_trackbed_vertices = new_sfile.get_vertices_by_prim_state(lod_dlevel, mt_trackbed)
        
            for mb_sleeperbase_vertex in mb_sleeperbase_vertices:
                mb_sleeperbase_vertex.point.y = 0.120 # Not needed, so set height below slab track surface
                new_sfile.update_vertex(mb_sleeperbase_vertex)
            
            for mb_trackbed_vertex in mb_trackbed_vertices:
                closest_centerpoint = tsu.find_closest_centerpoint(mb_trackbed_vertex.point, trackcenter, plane='xz')
                distance_from_center = tsu.signed_distance_between(mb_trackbed_vertex.point, closest_centerpoint, plane="xz")

                # Innermost mb_trackbed points
                if distance_from_center < -1.65 and distance_from_center > -1.75:
                    new_position = tsu.get_new_position_from_trackcenter(-1.4125, mb_trackbed_vertex.point, trackcenter)
                    mb_trackbed_vertex.point.x = new_position.x # Set recalculated x
                    mb_trackbed_vertex.point.y = 0.02 # Set height
                    mb_trackbed_vertex.point.z = new_position.z # Set recalculated z
                    new_sfile.update_vertex(mb_trackbed_vertex)
                if distance_from_center > 1.65 and distance_from_center < 1.75:
                    new_position = tsu.get_new_position_from_trackcenter(1.4125, mb_trackbed_vertex.point, trackcenter)
                    mb_trackbed_vertex.point.x = new_position.x # Set recalculated x
                    mb_trackbed_vertex.point.y = 0.02 # Set height
                    mb_trackbed_vertex.point.z = new_position.z # Set recalculated z
                    new_sfile.update_vertex(mb_trackbed_vertex)
                
                # Outermost mb_trackbed points
                if distance_from_center < -2.55 and distance_from_center > -2.65:
                    new_position = tsu.get_new_position_from_trackcenter(-2.4325, mb_trackbed_vertex.point, trackcenter)
                    mb_trackbed_vertex.point.x = new_position.x # Set recalculated x
                    mb_trackbed_vertex.point.y = 0.01 # Set height
                    mb_trackbed_vertex.point.z = new_position.z # Set recalculated z
                    new_sfile.update_vertex(mb_trackbed_vertex)
                if distance_from_center > 2.55 and distance_from_center < 2.65:
                    new_position = tsu.get_new_position_from_trackcenter(2.4325, mb_trackbed_vertex.point, trackcenter)
                    mb_trackbed_vertex.point.x = new_position.x # Set recalculated x
                    mb_trackbed_vertex.point.y = 0.01 # Set height
                    mb_trackbed_vertex.point.z = new_position.z # Set recalculated z
                    new_sfile.update_vertex(mb_trackbed_vertex)

            for mt_trackbed_vertex in mt_trackbed_vertices:
                closest_centerpoint = tsu.find_closest_centerpoint(mt_trackbed_vertex.point, trackcenter, plane='xz')
                distance_from_center = tsu.signed_distance_between(mt_trackbed_vertex.point, closest_centerpoint, plane="xz")

                # Second to last outermost mt_trackbed points
                if distance_from_center < -1.25 and distance_from_center > -1.35:
                    new_position = tsu.get_new_position_from_trackcenter(-1.4025, mt_trackbed_vertex.point, trackcenter)
                    mt_trackbed_vertex.point.x = new_position.x # Set recalculated x
                    mt_trackbed_vertex.point.y = 0.128 # Set height
                    mt_trackbed_vertex.point.z = new_position.z # Set recalculated z
                    if mt_trackbed_vertex.uv_point.u == 0.6357:
                        mt_trackbed_vertex.uv_point.u = 0.6582
                    elif mt_trackbed_vertex.uv_point.u == 0.0918:
                        mt_trackbed_vertex.uv_point.u = 0.0693
                    new_sfile.update_vertex(mt_trackbed_vertex)
                if distance_from_center > 1.25 and distance_from_center < 1.35:
                    new_position = tsu.get_new_position_from_trackcenter(1.4025, mt_trackbed_vertex.point, trackcenter)
                    mt_trackbed_vertex.point.x = new_position.x # Set recalculated x
                    mt_trackbed_vertex.point.y = 0.128 # Set height
                    mt_trackbed_vertex.point.z = new_position.z # Set recalculated z
                    if mt_trackbed_vertex.uv_point.u == 0.1143:
                        mt_trackbed_vertex.uv_point.u = 0.0918
                    elif mt_trackbed_vertex.uv_point.u == 0.6582:
                        mt_trackbed_vertex.uv_point.u = 0.6807
                    new_sfile.update_vertex(mt_trackbed_vertex)
                
                # Outermost mt_trackbed points
                if distance_from_center < -1.65 and distance_from_center > -1.75:
                    new_position = tsu.get_new_position_from_trackcenter(-1.4125, mt_trackbed_vertex.point, trackcenter)
                    mt_trackbed_vertex.point.x = new_position.x # Set recalculated x
                    mt_trackbed_vertex.point.y = 0.02 # Set height
                    mt_trackbed_vertex.point.z = new_position.z # Set recalculated z
                    if mt_trackbed_vertex.uv_point.u == 0.7158:
                        mt_trackbed_vertex.uv_point.u = 0.6758
                    elif mt_trackbed_vertex.uv_point.u == 0.0742:
                        mt_trackbed_vertex.uv_point.u = 0.0342
                    new_sfile.update_vertex(mt_trackbed_vertex)
                if distance_from_center > 1.65 and distance_from_center < 1.75:
                    new_position = tsu.get_new_position_from_trackcenter(1.4125, mt_trackbed_vertex.point, trackcenter)
                    mt_trackbed_vertex.point.x = new_position.x # Set recalculated x
                    mt_trackbed_vertex.point.y = 0.02 # Set height
                    mt_trackbed_vertex.point.z = new_position.z # Set recalculated z
                    if mt_trackbed_vertex.uv_point.u == 0.0342:
                        mt_trackbed_vertex.uv_point.u = 0.0742
                    elif mt_trackbed_vertex.uv_point.u == 0.6758:
                        mt_trackbed_vertex.uv_point.u = 0.7158
                    new_sfile.update_vertex(mt_trackbed_vertex)
        
        new_sfile.save()
        new_sfile.compress(ffeditc_path)

        # Convert .sd file
        sdfile_name = sfile_name.replace(".s", ".sd")
        new_sdfile_name = new_sfile_name.replace(".s", ".sd")

        sdfile = tsu.load_file(sdfile_name, shape_load_path)
        new_sdfile = sdfile.copy(new_filename=new_sdfile_name, new_directory=shape_processed_path)
        new_sdfile.replace_ignorecase(sfile_name, new_sfile_name)
        new_sdfile.save()
