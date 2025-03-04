import tsu
import shutil
import re
import numpy as np


if __name__ == "__main__":
    shape_load_path = "..\\..\\..\\..\\Content\\PGA DK24\\GLOBAL\\SHAPES"
    shape_converted_path = ".\\Tunnels_500r2_5d"
    ffeditc_path = ".\\ffeditc_unicode.exe"
    match_shapes = "DB*t500r5d*Tun*.s"
    ignore_shapes = []
    
    trackshape_names = tsu.find_trackshape_names(shape_load_path, match_shapes, ignore_shapes)

    tsu.ensure_directory_exists(shape_converted_path)

    for original_shape_name in trackshape_names:
        print("File %d of %d..." % (trackshape_names.index(original_shape_name), len(trackshape_names)))

        original_shape_sdname = original_shape_name.replace(".s", ".sd")
        converted_shape_name = original_shape_name.replace("r5d", "r2_5d")
        converted_shape_sdname = converted_shape_name.replace(".s", ".sd")
        original_sfile = "%s\\%s" % (shape_load_path, original_shape_name)
        original_sdfile = "%s\\%s" % (shape_load_path, original_shape_sdname)
        converted_sfile = "%s\\%s" % (shape_converted_path, converted_shape_name)
        converted_sdfile = "%s\\%s" % (shape_converted_path, converted_shape_sdname)

        track_length = None
        curve_radius = None
        curve_angle = None
        center_points = None

        if "strt" in original_shape_name.lower():
            match = re.search(r'a(\d+)t(\d+)([m])', original_shape_name.lower())

            if match:
                track_length = int(match.group(2))

            if track_length is not None:
                center_points = tsu.generate_straight_centerpoints(length=track_length)
        else:
            match_radius = re.search(r'a(\d+)t(\d+)(r)', original_shape_name.lower())
            match_angle = re.search(r'r(\d+)(d)', original_shape_name.lower())

            if match_radius:
                curve_radius = int(match_radius.group(2))

            if match_angle:
                curve_angle = -int(match_angle.group(1))

            if curve_radius is not None and curve_angle is not None:
                center_points = tsu.generate_curve_centerpoints(radius=curve_radius, degrees=curve_angle)
        
        if center_points is None:
            print("Unable to parse shape name '%s', skipping..." % (original_shape_name))
            continue

        shutil.copyfile(original_sfile, converted_sfile)
        shutil.copyfile(original_sdfile, converted_sdfile)

        tsu.decompress_shape(ffeditc_path, converted_sfile)

        sfile_text = tsu.read_file(converted_sfile)

        sfile_lines = sfile_text.split("\n")
        
        point_idxs = tsu.get_point_idxs_by_prim_state_name(sfile_lines)
        current_point_idx = 0

        for line_idx in range(0, len(sfile_lines)):
            sfile_line = sfile_lines[line_idx]
            if "\t\tpoint (" in sfile_line.lower():
                parts = sfile_line.split(" ")

                point = np.array([float(parts[2]), float(parts[3]), float(parts[4])])

                distance_along_track = tsu.distance_along_curved_track(point, center_points, curve_radius, -2.5)
                
                if distance_along_track[0] < -2.5:
                    new_xz_position = tsu.get_new_position_from_angle(curve_radius, -2.5, point, center_points)
                    parts[2] = str(new_xz_position[0]) # Set recalculated x
                    parts[4] = str(new_xz_position[2]) # Set recalculated z

                sfile_lines[line_idx] = " ".join(parts)
                current_point_idx += 1
        
        sfile_text = "\n".join(sfile_lines)
        tsu.write_file(converted_sfile, sfile_text)

        tsu.compress_shape(ffeditc_path, converted_sfile)

        sdfile_text = tsu.read_file(converted_sdfile)
        sdfile_text = tsu.replace_ignorecase(sdfile_text, original_shape_name, converted_shape_name)
        tsu.write_file(converted_sdfile, sdfile_text)
