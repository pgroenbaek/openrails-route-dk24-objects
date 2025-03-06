import trackshapeutils as tsu
import shutil


if __name__ == "__main__":
    shape_load_path = "..\\..\\..\\..\\Content\\PGA DK24\\GLOBAL\\SHAPES"
    shape_converted_path = ".\\Converted_from_DB1zpnt_to_V4hsRKLpnt"
    ffeditc_path = ".\\ffeditc_unicode.exe"
    match_shapes = "DB1z_*Pnt*.s"
    ignore_shapes = ["*Tun*", "*EndPnt*", "*Frog*"]
    
    trackshape_names = tsu.find_trackshape_names(shape_load_path, match_shapes, ignore_shapes)

    tsu.ensure_directory_exists(shape_converted_path)

    for original_shape_name in trackshape_names:
        print("File %d of %d..." % (trackshape_names.index(original_shape_name), len(trackshape_names)))

        original_shape_sdname = original_shape_name.replace(".s", ".sd")
        converted_shape_name = original_shape_name.replace("DB1z_", "V4hs1t_RKL_").replace("A1t", "").replace("a1t", "")
        converted_shape_sdname = converted_shape_name.replace(".s", ".sd")
        original_sfile = "%s\\%s" % (shape_load_path, original_shape_name)
        original_sdfile = "%s\\%s" % (shape_load_path, original_shape_sdname)
        converted_sfile = "%s\\%s" % (shape_converted_path, converted_shape_name)
        converted_sdfile = "%s\\%s" % (shape_converted_path, converted_shape_sdname)

        shutil.copyfile(original_sfile, converted_sfile)
        shutil.copyfile(original_sdfile, converted_sdfile)

        tsu.decompress_shape(ffeditc_path, converted_sfile)

        sfile_text = tsu.read_file(converted_sfile)
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_Rails1.ace", "V4_Rails1.ace")
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_Rails1w.ace", "V4_Rails1.ace")
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_Track1.ace", "V4_RKLb.ace")
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_Track1s.ace", "V4_RKLs.ace")
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_Track1w.ace", "V4_RKLb.ace")
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_Track1sw.ace", "V4_RKLs.ace")
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_TrackSfs1.ace", "V4_RKLb.ace")
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_TrackSfs1s.ace", "V4_RKLs.ace")
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_TrackSfs1w.ace", "V4_RKLb.ace")
        sfile_text = tsu.replace_ignorecase(sfile_text, "DB_TrackSfs1sw.ace", "V4_RKLs.ace")

        # RKL side
        # [Vector((-1.4025001525878906, 0.0, -0.12800000607967377))]
        # [Vector((-1.4125001430511475, 0.0, -0.019999999552965164))]
        # [Vector((-2.43250036239624, 0.0, 0.009999999776482582))]

        # normal track side
        # [Vector((-1.2999999523162842, 0.0, -0.13499999046325684))]
        # [Vector((-1.7000000476837158, 0.0, -0.13589999079704285))]
        # [Vector((-2.5999999046325684, 0.0, 0.019999999552965164))]

        sfile_lines = sfile_text.split("\n")
        
        center_points = tsu.generate_straight_centerpoints(length=100)
        point_idxs = tsu.get_point_idxs_by_prim_state_name(sfile_lines)
        uv_point_idxs = tsu.get_uv_point_idxs(sfile_lines)
        current_point_idx = 0

        # TODO: This is very experimental and by no means done yet.
        for line_idx in range(0, len(sfile_lines)):
            sfile_line = sfile_lines[line_idx]
            if "\t\tpoint (" in sfile_line.lower():
                parts = sfile_line.split(" ")

                is_mt_trackbed = False if "DB_Track2w" not in point_idxs else current_point_idx in point_idxs["DB_Track2w"]
                is_mb_trackbed = False if "DB_Track2sw" not in point_idxs else current_point_idx in point_idxs["DB_Track2sw"]

                if is_mt_trackbed:
                    point = np.array([float(parts[2]), float(parts[3]), float(parts[4])])
                    closest_center_point = tsu.find_closest_center_point(point, center_points, plane='xz')
                    distance_from_center = tsu.signed_distance_from_center(point, center=closest_center_point, plane="xz")

                    # Second to last outermost mt_trackbed points
                    if distance_from_center < -1.25 and distance_from_center > -1.35:
                        new_xz_position = tsu.get_new_position_from_trackcenter(-1.4025, point, center_points)
                        parts[2] = str(new_xz_position[0]) # Set recalculated x
                        parts[3] = "0.128" # Set height
                        parts[4] = str(new_xz_position[2]) # Set recalculated z
                        u_value, v_value = tsu.get_uv_point_value(sfile_lines, uv_point_idxs[current_point_idx])
                        u_value = 0.0918
                        tsu.set_uv_point_value(sfile_lines, uv_point_idxs[current_point_idx], u_value, v_value)
                    if distance_from_center > 1.25 and distance_from_center < 1.35:
                        new_xz_position = tsu.get_new_position_from_trackcenter(1.4025, point, center_points)
                        parts[2] = str(new_xz_position[0]) # Set recalculated x
                        parts[3] = "0.128" # Set height
                        parts[4] = str(new_xz_position[2]) # Set recalculated z
                        u_value, v_value = tsu.get_uv_point_value(sfile_lines, uv_point_idxs[current_point_idx])
                        u_value = 0.6582
                        tsu.set_uv_point_value(sfile_lines, uv_point_idxs[current_point_idx], u_value, v_value)
                    
                    # Outermost mt_trackbed points
                    if distance_from_center < -1.65 and distance_from_center > -1.75:
                        new_xz_position = tsu.get_new_position_from_trackcenter(-1.4125, point, center_points)
                        parts[2] = str(new_xz_position[0]) # Set recalculated x
                        parts[3] = "0.02" # Set height
                        parts[4] = str(new_xz_position[2]) # Set recalculated z
                        u_value, v_value = tsu.get_uv_point_value(sfile_lines, uv_point_idxs[current_point_idx])
                        u_value = 0.0742
                        tsu.set_uv_point_value(sfile_lines, uv_point_idxs[current_point_idx], u_value, v_value)
                    if distance_from_center > 1.65 and distance_from_center < 1.75:
                        new_xz_position = tsu.get_new_position_from_trackcenter(1.4125, point, center_points)
                        parts[2] = str(new_xz_position[0]) # Set recalculated x
                        parts[3] = "0.02" # Set height
                        parts[4] = str(new_xz_position[2]) # Set recalculated z
                        u_value, v_value = tsu.get_uv_point_value(sfile_lines, uv_point_idxs[current_point_idx])
                        u_value = 0.6758
                        tsu.set_uv_point_value(sfile_lines, uv_point_idxs[current_point_idx], u_value, v_value)
                
                if is_mb_trackbed:
                    point = np.array([float(parts[2]), float(parts[3]), float(parts[4])])
                    closest_center_point = tsu.find_closest_center_point(point, center_points, plane='xz')
                    distance_from_center = tsu.signed_distance_from_center(point, center=closest_center_point, plane="xz")

                    # Innermost mb_trackbed points
                    if distance_from_center < -1.65 and distance_from_center > -1.75:
                        new_xz_position = tsu.get_new_position_from_trackcenter(-1.4125, point, center_points)
                        parts[2] = str(new_xz_position[0]) # Set recalculated x
                        parts[3] = "0.02" # Set height
                        parts[4] = str(new_xz_position[2]) # Set recalculated z
                        u_value, v_value = tsu.get_uv_point_value(sfile_lines, uv_point_idxs[current_point_idx])
                        u_value = 0.6758
                        tsu.set_uv_point_value(sfile_lines, uv_point_idxs[current_point_idx], u_value, v_value)
                    if distance_from_center > 1.65 and distance_from_center < 1.75:
                        new_xz_position = tsu.get_new_position_from_trackcenter(1.4125, point, center_points)
                        parts[2] = str(new_xz_position[0]) # Set recalculated x
                        parts[3] = "0.02" # Set height
                        parts[4] = str(new_xz_position[2]) # Set recalculated z
                        u_value, v_value = tsu.get_uv_point_value(sfile_lines, uv_point_idxs[current_point_idx])
                        u_value = 0.6758
                        tsu.set_uv_point_value(sfile_lines, uv_point_idxs[current_point_idx], u_value, v_value)
                    
                    # Outermost mb_trackbed points
                    if distance_from_center < -2.55 and distance_from_center > -2.65:
                        new_xz_position = tsu.get_new_position_from_trackcenter(-2.4325, point, center_points)
                        parts[2] = str(new_xz_position[0]) # Set recalculated x
                        parts[3] = "0.01" # Set height
                        parts[4] = str(new_xz_position[2]) # Set recalculated z
                        u_value, v_value = tsu.get_uv_point_value(sfile_lines, uv_point_idxs[current_point_idx])
                        u_value = 0.8620
                        tsu.set_uv_point_value(sfile_lines, uv_point_idxs[current_point_idx], u_value, v_value)
                    if distance_from_center > 2.55 and distance_from_center < 2.65:
                        new_xz_position = tsu.get_new_position_from_trackcenter(2.4325, point, center_points)
                        parts[2] = str(new_xz_position[0]) # Set recalculated x
                        parts[3] = "0.01" # Set height
                        parts[4] = str(new_xz_position[2]) # Set recalculated z
                        u_value, v_value = tsu.get_uv_point_value(sfile_lines, uv_point_idxs[current_point_idx])
                        u_value = 0.8620
                        tsu.set_uv_point_value(sfile_lines, uv_point_idxs[current_point_idx], u_value, v_value)
                
                sfile_lines[line_idx] = " ".join(parts)
                current_point_idx += 1
        
        sfile_text = "\n".join(sfile_lines)
        tsu.write_file(converted_sfile, sfile_text)

        tsu.compress_shape(ffeditc_path, converted_sfile)

        sdfile_text = tsu.read_file(converted_sdfile)
        sdfile_text = tsu.replace_ignorecase(sdfile_text, original_shape_name, converted_shape_name)
        tsu.write_file(converted_sdfile, sdfile_text)