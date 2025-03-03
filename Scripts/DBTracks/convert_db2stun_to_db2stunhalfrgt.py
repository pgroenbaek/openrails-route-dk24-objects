import os
import fnmatch
import subprocess
import shutil
import re
import numpy as np
from scipy.spatial import KDTree
from scipy.interpolate import splprep, splev


def find_trackshape_names(shape_path, match_shapes, ignore_shapes):
    """
    Find and return a list of track shape file names in the specified directory 
    that match a given pattern while excluding those that match the ignore list.

    Parameters:
        shape_path (str): Path to the directory containing shape files.
        match_shapes (str): Pattern to match shape files.
        ignore_shapes (list): List of patterns to ignore.

    Returns:
        list: List of shape file names that match the criteria.
    """
    track_shapes = []
    for file_name in os.listdir(shape_path):
        if fnmatch.fnmatch(file_name, match_shapes):
            if any([fnmatch.fnmatch(file_name, x) for x in ignore_shapes]):
                continue
            track_shapes.append(file_name)
    return track_shapes


def ensure_directory_exists(path):
    """
    Ensure that a given directory exists, creating it if necessary.

    Parameters:
        path (str): Path of the directory to check or create.
    """
    if not os.path.exists(path):
        os.makedirs(path)


def read_file(file_path, encoding='utf-16'):
    """
    Read and return the content of a file with the specified encoding.

    Parameters:
        file_path (str): Path to the file to read.
        encoding (str, optional): File encoding (default is 'utf-16').

    Returns:
        str: Content of the file.
    """
    with open(file_path, 'r', encoding=encoding) as f:
        return f.read()


def write_file(file_path, text, encoding='utf-16'):
    """
    Write the given text to a file with the specified encoding.

    Parameters:
        file_path (str): Path to the file to write.
        text (str): Text to write into the file.
        encoding (str, optional): File encoding (default is 'utf-16').
    """
    with open(file_path, 'w', encoding=encoding) as f:
        f.write(text)


def is_binary_string(bytes):
    """
    Determine if a given byte sequence represents binary data.

    Parameters:
        bytes (bytes): Byte sequence to check.

    Returns:
        bool: True if the data is binary, False otherwise.
    """
    textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
    return bool(bytes.translate(None, textchars))


def compress_shape(ffeditc_path, shape_file):
    """
    Compress a shape file using ffeditc if it is not already binary.

    Parameters:
        ffeditc_path (str): Path to the ffeditc executable.
        shape_file (str): Path to the shape file to compress.
    """
    if not is_binary_string(open(shape_file, 'rb').read(256)):
        subprocess.call([ffeditc_path, shape_file, "/o:" + shape_file])


def decompress_shape(ffeditc_path, shape_file):
    """
    Decompress a shape file using ffeditc if it is in binary format.

    Parameters:
        ffeditc_path (str): Path to the ffeditc executable.
        shape_file (str): Path to the shape file to decompress.
    """
    if is_binary_string(open(shape_file, 'rb').read(256)):
        subprocess.call([ffeditc_path, shape_file, "/u", "/o:" + shape_file])


def replace_ignorecase(text, search_exp, replace_str):
    """
    Replace occurrences of a pattern in a given text, ignoring case.

    Parameters:
        text (str): The original text.
        search_exp (str): The regular expression pattern to search for.
        replace_str (str): The replacement string.

    Returns:
        str: The modified text with replacements applied.
    """
    pattern = re.compile(search_exp, re.IGNORECASE)
    return pattern.sub(replace_str, text)


def generate_straight_centerpoints(length, num_points=1000, start_point=np.array([0, 0, 0])):
    """
    Generate centerpoints for a straight railway track in 3D space.

    Parameters:
    - length: Length of the straight track.
    - num_points: Number of points to generate along the track.
    - start_point: The starting point of the track in 3D space (default is the origin [0, 0, 0]).

    Returns:
    - np.array of shape (num_points, 3): Railway track points along the straight track in 3D space.
    """
    z = np.linspace(start_point[0], start_point[0] + length, num_points)
    x = np.full_like(z, start_point[1])
    y = np.full_like(z, start_point[2])

    return np.vstack((x, y, z)).T


def generate_curve_centerpoints(radius, degrees, num_points=1000):
    """
    Generate center points of a curve in 3D space, curving in the X-Z plane.

    Parameters:
    - radius: Radius of the curve (meters).
    - degrees: Total angle of the curve in degrees (negative = left curve, positive = right curve).
    - num_points: Number of points to generate along the curve.

    Returns:
    - np.array of shape (num_points, 3): Railway track points in 3D space with positive z-values.
    """
    theta = np.radians(np.linspace(0, abs(degrees), num_points))

    z = radius * np.sin(theta)
    x = radius * (1 - np.cos(theta))
    y = np.zeros_like(x)

    if degrees < 0:
        x = -x

    return np.vstack((x, y, z)).T


def find_closest_center_point(point_along_track, center_points, plane='xz'):
    """
    Finds the closest track center point to a given point along the track, with the option 
    to compute the closest point in the specified plane (XY or XZ).

    Args:
        point_along_track (numpy.ndarray): A 3D coordinate (x, y, z) representing a point somewhere on the track.
        center_points (numpy.ndarray): A 2D array of points (num_points, 3), each representing a centerpoint along the track.
        plane (str, optional): The plane to project onto ('xy' or 'xz'). Defaults to 'xz'.
    
    Returns:
        numpy.ndarray: The closest point on the track to the given point in the specified plane.
    """
    if plane == 'xz':
        center_points_2d = center_points[:, [0, 2]]
        point_2d = point_along_track[[0, 2]]
    elif plane == 'xy':
        center_points_2d = center_points[:, [0, 1]]
        point_2d = point_along_track[[0, 1]]
    else:
        raise ValueError("Invalid plane. Choose either 'xy' or 'xz'.")
    
    distances = np.linalg.norm(center_points_2d - point_2d, axis=1)
    
    closest_index = np.argmin(distances)
    
    return center_points[closest_index]


def signed_distance_from_center(point, center=np.array([0, 0, 0]), plane="xz"):
    """
    Computes the signed distance of a point from a given center in the specified plane.

    Args:
        point (numpy.ndarray): A 3D coordinate (x, y, z) representing the point.
        center (numpy.ndarray, optional): A 3D coordinate (x, y, z) representing the center. 
                                          Defaults to (0, 0, 0).
        plane (str, optional): The axis or plane to consider ('x', 'y', 'xy', 'xz', or 'z'). Defaults to 'xz'.

    Returns:
        float: The signed distance of the point from the center in the specified plane.
    """
    if plane == "x":
        point_proj = np.array([point[0], 0, 0])
        center_proj = np.array([center[0], 0, 0])
        reference_vector = np.array([0, 1, 0])
    elif plane == "y":
        point_proj = np.array([0, point[1], 0])
        center_proj = np.array([0, center[1], 0])
        reference_vector = np.array([1, 0, 0])
    elif plane == "xy":
        point_proj = np.array([point[0], point[1], 0])
        center_proj = np.array([center[0], center[1], 0])
        reference_vector = np.array([1, 0, 0])
    elif plane == "xz":
        point_proj = np.array([point[0], 0, point[2]])
        center_proj = np.array([center[0], 0, center[2]])
        reference_vector = np.array([0, 1, 0])
    elif plane == "z":
        point_proj = np.array([0, 0, point[2]])
        center_proj = np.array([0, 0, center[2]])
        reference_vector = np.array([1, 0, 0])
    else:
        raise ValueError("Invalid plane. Choose 'x', 'y', 'xy', 'xz', or 'z'.")

    vector_to_point = point_proj - center_proj
    cross = np.cross(reference_vector, vector_to_point)

    signed_distance = np.linalg.norm(vector_to_point[:2]) * np.sign(cross[-1])

    return signed_distance


def distance_along_track(point, center_points):
    """
    Computes the distance along the track to the closest point on the track.

    Args:
        point (numpy.ndarray): A 2D or 3D coordinate (x, y, [z]) representing the point.
        center_points (numpy.ndarray): A (N, 2) or (N, 3) array representing the track center points.

    Returns:
        tuple:
            - float: The cumulative distance along the track to the closest center point.
            - numpy.ndarray: The closest track center point.
    """
    tck, _ = splprep(center_points.T, s=0)
    num_samples = 1000
    u_values = np.linspace(0, 1, num_samples)
    spline_points = np.array(splev(u_values, tck)).T

    tree = KDTree(spline_points)
    distance, index = tree.query(point)

    cumulative_distance = np.cumsum(
        np.linalg.norm(np.diff(spline_points, axis=0), axis=1)
    )
    cumulative_distance = np.insert(cumulative_distance, 0, 0)  

    return cumulative_distance[index], spline_points[index]


def get_curve_point_from_angle(radius, angle_degrees):
    """
    Compute the (x, y, z) position given an angle from the start of the track.

    Parameters:
    - radius: Radius of the railway track curve.
    - angle_degrees: Angle from the starting position (0 degrees).

    Returns:
    - np.array([x, y, z]): The position in 3D space.
    """
    theta = np.radians(angle_degrees)
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    z = 0

    return np.array([x, y, z])


def get_new_position_from_angle(radius, angle_degrees, original_point, curve_center):
    """
    Compute the new (x, y, z) position of a point given an absolute angle from the start of the curve.

    Parameters:
    - radius: Radius of the railway track curve.
    - angle_degrees: Angle from the start of the track curve (not relative to original_point).
    - original_point: The (x, y, z) coordinate of the point to transform.
    - curve_center: The (x, y, z) coordinate of the curve's center.

    Returns:
    - np.array([x, y, z]): The new transformed position in 3D space.
    """
    theta = np.radians(angle_degrees)
    new_closest_x = curve_center[0] + radius * np.sin(theta)
    new_closest_z = curve_center[2] + radius * np.cos(theta)
    new_closest_point = np.array([new_closest_x, 0, new_closest_z])

    rotation_matrix = np.array([
        [np.cos(theta), 0, np.sin(theta)],
        [0, 1, 0],
        [-np.sin(theta), 0, np.cos(theta)]
    ])

    rotated_offset = rotation_matrix @ original_point

    new_position = new_closest_point + rotated_offset
    return new_position


def get_point_idxs_by_prim_state_name(sfile_lines):
    """
    Extracts and organizes point indices by their associated prim_state names from a given list of shape file lines.

    This function processes a list of lines from a shape file, identifying vertices and their corresponding point 
    indices, as well as primitive state names. For each prim_state, it collects the relevant point indices 
    by mapping vertex indices (from `vertex_idxs`) to their point indices (from `vertex`). The point indices 
    are then organized by their associated prim_state name.

    Args:
        sfile_lines (list of str): A list of strings representing the lines from a shape file.

    Returns:
        dict: A dictionary where the keys are `prim_state_name` strings, and the values are lists of unique point indices
              associated with that prim_state.
    """
    points_by_prim_state_name = {}
    current_prim_state_name = None
    processing_primitives = False
    collecting_vertex_idxs = False
    current_vertex_indices = []
    vertices_map = {}

    prim_state_names = extract_prim_state_names(sfile_lines)

    for sfile_line in sfile_lines:
        if 'sub_object (' in sfile_line.lower():
            vertices_map = []

        if 'vertex ' in sfile_line.lower():
            parts = sfile_line.split()
            if len(parts) > 3:
                point_idx = int(parts[3])
                vertices_map.append(point_idx)

        if 'prim_state_idx' in sfile_line.lower():
            parts = sfile_line.split(" ")
            current_prim_state_name = prim_state_names[int(parts[2])]
            if current_prim_state_name not in points_by_prim_state_name:
                points_by_prim_state_name[current_prim_state_name] = []
        
        if 'indexed_trilist' in sfile_line.lower():
            processing_primitives = True
            current_vertex_indices = []

        if 'vertex_idxs' in sfile_line.lower() or collecting_vertex_idxs:
            parts = sfile_line.replace('vertex_idxs', '').replace('(', '').replace(')', '').split()
            if parts:
                if not collecting_vertex_idxs:
                    parts = parts[1:]
                current_vertex_indices.extend(map(int, parts))
            collecting_vertex_idxs = not sfile_line.endswith(')')

        if processing_primitives and ')' in sfile_line.lower() and current_vertex_indices:
            for vertex_idx in current_vertex_indices:
                point_index = vertices_map[vertex_idx]
                if point_index not in points_by_prim_state_name[current_prim_state_name]:
                    points_by_prim_state_name[current_prim_state_name].append(point_index)
            processing_primitives = False

    return points_by_prim_state_name


def extract_prim_state_names(sfile_lines):
    """
    Extracts the prim_state names from a shape.
    
    Args:
        sfile_lines (list of str): A list of strings representing lines from the shape file.
    
    Returns:
        list: The list of prim_state names indexed by prim_state_idx.
    """
    prim_state_names = []

    for sfile_line in sfile_lines:
        if "prim_state " in sfile_line.lower():
            parts = sfile_line.split()
            prim_state_names.append(parts[1])

    return prim_state_names



if __name__ == "__main__":
    shape_load_path = "..\\..\\..\\..\\Content\\PGA DK24\\GLOBAL\\SHAPES"
    shape_converted_path = ".\\Converted_from_DB2sTun_to_DB2sTunHalfRgt"
    ffeditc_path = ".\\ffeditc_unicode.exe"
    match_shapes = "DB2s_*Tun*.s"
    ignore_shapes = ["*Pnt*", "*Frog*", "*Half*"]
    
    trackshape_names = find_trackshape_names(shape_load_path, match_shapes, ignore_shapes)

    ensure_directory_exists(shape_converted_path)

    for original_shape_name in trackshape_names:
        print("File %d of %d..." % (trackshape_names.index(original_shape_name), len(trackshape_names)))
        
        original_shape_sdname = original_shape_name.replace(".s", ".sd")
        converted_shape_name = original_shape_name.replace(".s", "_HalfRgt.s")
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
                center_points = generate_straight_centerpoints(length=track_length)
        else:
            match_radius = re.search(r'a(\d+)t(\d+)(r)', original_shape_name.lower()) 
            match_angle = re.search(r'r(\d+)(d)', original_shape_name.lower())

            if match_radius:
                curve_radius = int(match_radius.group(2))

            if match_angle:
                curve_angle = -int(match_angle.group(1))

            if curve_radius is not None and curve_angle is not None:
                center_points = generate_curve_centerpoints(radius=curve_radius, degrees=curve_angle)
        
        if center_points is None:
            print("Unable to parse shape name '%s', skipping..." % (original_shape_name))
            continue

        shutil.copyfile(original_sfile, converted_sfile)
        shutil.copyfile(original_sdfile, converted_sdfile)

        decompress_shape(ffeditc_path, converted_sfile)

        sfile_text = read_file(converted_sfile)
        sfile_lines = sfile_text.split("\n")
        
        point_idxs = get_point_idxs_by_prim_state_name(sfile_lines)
        current_point_idx = 0

        for line_idx in range(0, len(sfile_lines)):
            sfile_line = sfile_lines[line_idx]
            if "\t\tpoint (" in sfile_line.lower():
                parts = sfile_line.split(" ")

                is_tunnel_wall = current_point_idx in point_idxs["mt_tunwall"]
                is_tunnel_roof = False if "mt_tun_roof" not in point_idxs else current_point_idx in point_idxs["mt_tun_roof"]

                if is_tunnel_wall or is_tunnel_roof:
                    point = np.array([float(parts[2]), float(parts[3]), float(parts[4])])
                    closest_center_point = find_closest_center_point(point, center_points, plane='xz')
                    distance_from_center = signed_distance_from_center(point, center=closest_center_point, plane="xz")

                    if distance_from_center > 0: # Right of track center
                        parts[3] = "8.45" # Set height
                
                sfile_lines[line_idx] = " ".join(parts)
                current_point_idx += 1
        
        sfile_text = "\n".join(sfile_lines)
        write_file(converted_sfile, sfile_text)

        compress_shape(ffeditc_path, converted_sfile)

        sdfile_text = read_file(converted_sdfile)
        sdfile_text = replace_ignorecase(sdfile_text, original_shape_name, converted_shape_name)
        write_file(converted_sdfile, sdfile_text)
