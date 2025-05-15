import os
import re
import trackshapeutils as tsu

if __name__ == "__main__":
    shape_load_path = "../../../../Content/PGA DK24/GLOBAL/SHAPES"
    shape_processed_path = "./Processed/DB2sTunHalfRgt"
    ffeditc_path = "./ffeditc_unicode.exe"
    match_shapes = ["DB2s_*Tun*.s"]
    ignore_shapes = ["*Pnt*", "*Frog*"]
    
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
        new_sfile_name = sfile_name.replace(".s", "_HalfRgt.s")

        sfile = tsu.load_shape(sfile_name, shape_load_path)
        new_sfile = sfile.copy(new_filename=new_sfile_name, new_directory=shape_processed_path)
        new_sfile.decompress(ffeditc_path)

        lod_dlevels = new_sfile.get_lod_dlevels()
        mt_tunwall = new_sfile.get_prim_state_by_name("mt_tunwall")
        mt_tun_roof = new_sfile.get_prim_state_by_name("mt_tun_roof")
        for lod_dlevel in lod_dlevels:
            vertices = new_sfile.get_vertices_by_prim_state(lod_dlevel, mt_tunwall)
            vertices += new_sfile.get_vertices_by_prim_state(lod_dlevel, mt_tun_roof)
        
            for vertex in vertices:
                closest_centerpoint = tsu.find_closest_centerpoint(vertex.point, trackcenter, plane='xz')
                distance_from_center = tsu.signed_distance_between(vertex.point, closest_centerpoint, plane="xz")

                if distance_from_center > 0: # Right of track center
                    vertex.point.y = "8.45" # Set height
                    new_sfile.update_vertex(vertex)

        new_sfile.save()
        new_sfile.compress(ffeditc_path)

        # Process .sd file
        sdfile_name = sfile_name.replace(".s", ".sd")
        new_sdfile_name = new_sfile_name.replace(".s", ".sd")

        sdfile = tsu.load_file(sdfile_name, shape_load_path)
        new_sdfile = sdfile.copy(new_filename=new_sdfile_name, new_directory=shape_processed_path)
        new_sdfile.replace_ignorecase(sfile_name, new_sfile_name)
        new_sdfile.save()
