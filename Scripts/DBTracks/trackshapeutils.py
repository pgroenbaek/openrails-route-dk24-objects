import os
import fnmatch
import subprocess
import re
import numpy as np
from scipy.interpolate import splprep, splev
from scipy.spatial import KDTree

"""
tsu.py - Track Shape Utils

This module provides various utility functions for working with track shape files, 
including file handling, shape processing, and geometric calculations for track 
center points and curves. It includes functions for:

- File operations (reading, writing, ensuring directory existence)
- Shape file processing (finding track shape files, compression, and decompression)
- String and text manipulation (case-insensitive replacement)
- Geometric calculations for track center points (straight and curved track segments)
- Closest point searches and signed distance calculations
- Linking points to UV values and prim_state names
- Modification of UV values

This module is intended for use with existing track shapes to adjust them. Points in the
shape geometry can be repositioned, for example relative to the track center or along the track
for both curved and straight track shapes. This code cannot add/remove shape geometry, but you can
hide things underneath the trackbed. It will also not edit how vertices are connected.

Functions:
- find_trackshape_names(shape_path, match_shapes, ignore_shapes)
- ensure_directory_exists(path)
- read_file(file_path, encoding='utf-16')
- write_file(file_path, text, encoding='utf-16')
- is_compressed(shape_file)
- compress_shape(ffeditc_path, shape_file)
- decompress_shape(ffeditc_path, shape_file)
- replace_ignorecase(text, search_exp, replace_str)
- generate_straight_centerpoints(length, num_points=1000, start_point=np.array([0, 0, 0]))
- generate_curve_centerpoints(radius, degrees, num_points=1000)
- find_closest_center_point(point_along_track, center_points, plane='xz')
- signed_distance_from_center(point, center=np.array([0, 0, 0]), plane="xz")
- distance_along_curved_track(point, center_points, curve_angle, radius)
- distance_along_straight_track(point, center_points)
- get_curve_point_from_angle(radius, angle_degrees)
- get_new_position_from_angle(radius, angle_degrees, original_point, center_points)
- get_new_position_from_trackcenter(signed_distance, original_point, center_points)
- get_uv_point_idxs(sfile_lines)
- get_uv_point_value(sfile_lines, uv_point_idx)
- set_uv_point_value(sfile_lines, uv_point_idx, u_value, v_value)
- get_point_idxs_by_prim_state_name(sfile_lines)
- get_prim_state_names(sfile_lines)

Dependencies:
- os
- fnmatch
- re
- numpy
- scipy.interpolate (for spline calculations)
- scipy.spatial.KDTree (for closest point searches)
- subprocess (for calling external tools)

Author: Peter Grønbæk Andersen (pgroenbaek)
Date: 2025-03-04
Version: 0.1.0
License: GNU GPL v3
"""

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


def is_compressed(shape_file):
    """
    Determine if a shape file is compressed by inspecting the header.

    Parameters:
        shape_file (str): Shape file to check.

    Returns:
        bool: True if the shape file is compressed, False otherwise.
    """
    with open(shape_file, 'r', encoding='utf-16') as f:
        try:
            header = f.read(32)
            if header.startswith("SIMISA@@@@@@@@@@JINX0s1t______"):
                return False
        except UnicodeDecodeError:
            pass
        return True


def compress_shape(ffeditc_path, shape_file):
    """
    Compress a shape file using ffeditc if it is not already compressed.

    Parameters:
        ffeditc_path (str): Path to the ffeditc executable.
        shape_file (str): Path to the shape file to compress.
    """
    if not is_compressed(shape_file):
        subprocess.call([ffeditc_path, shape_file, "/o:" + shape_file])


def decompress_shape(ffeditc_path, shape_file):
    """
    Decompress a shape file using ffeditc if it is not already decompressed.

    Parameters:
        ffeditc_path (str): Path to the ffeditc executable.
        shape_file (str): Path to the shape file to decompress.
    """
    if is_compressed(shape_file):
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
    Generate center points for a straight track in 3D space.

    Parameters:
    - length: Length of the straight track in meters.
    - num_points: Number of points to generate along the track.
    - start_point: The starting point of the track in 3D space (default is the origin [0, 0, 0]).

    Returns:
    - np.array of shape (num_points, 3): Center points along the straight track in 3D space.
    """
    z = np.linspace(start_point[0], start_point[0] + length, num_points)
    x = np.full_like(z, start_point[1])
    y = np.full_like(z, start_point[2])

    return np.vstack((x, y, z)).T


def generate_curve_centerpoints(radius, degrees, num_points=1000):
    """
    Generate center points of a curve in 3D space, curving in the X-Z plane.

    Parameters:
    - radius: Radius of the curve in meters.
    - degrees: Total angle of the curve in degrees (negative = left curve, positive = right curve).
    - num_points: Number of points to generate along the curve.

    Returns:
    - np.array of shape (num_points, 3): Center points in 3D space with positive z-values.
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
        center_points (numpy.ndarray): A 2D array of points (num_points, 3), each representing a center point along the track.
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
    Computes the signed distance of a point from a given track center point in the specified plane.

    Args:
        point (numpy.ndarray): A 3D coordinate (x, y, z) representing the point.
        center (numpy.ndarray, optional): A 3D coordinate (x, y, z) representing the track center point. 
                                          Defaults to (0, 0, 0).
        plane (str, optional): The axis or plane to consider ('x', 'y', 'xy', 'xz', or 'z'). Defaults to 'xz'.

    Returns:
        float: The signed distance of the point from the track center point in the specified plane.
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


def distance_along_curved_track(point, center_points, curve_angle, radius):
    """
    Computes the distance along a curved track center to the closest center point,
    considering a constant curve angle, using only the XZ plane. Returns distance in degrees.

    Args:
        point (numpy.ndarray): A 3D coordinate (x, y, z) in meters.
        center_points (numpy.ndarray): A (N, 3) array representing track center points in meters.
        curve_angle (float): The constant curve angle in radians (negative for left, positive for right).
        radius (float): The constant curve radius in meters.

    Returns:
        tuple:
            - float: The cumulative distance along the track to the closest center point (in degrees).
            - numpy.ndarray: The closest track center point.
    """
    center_points_xz = center_points[:, [0, 2]]
    point_xz = point[[0, 2]]

    tck, _ = splprep(center_points_xz.T, s=0)
    
    num_samples = 1000
    u_values = np.linspace(0, 1, num_samples)
    spline_points_xz = np.array(splev(u_values, tck)).T

    tree = KDTree(spline_points_xz)
    _, index = tree.query(point_xz)

    arc_length = abs(curve_angle) * radius
    segment_lengths = np.linalg.norm(np.diff(spline_points_xz, axis=0), axis=1)
    
    cumulative_distance = np.cumsum(np.full_like(segment_lengths, arc_length))
    cumulative_distance = np.insert(cumulative_distance, 0, 0)

    meters_to_degrees = 1 / 111320
    cumulative_distance_degrees = cumulative_distance * meters_to_degrees

    return cumulative_distance_degrees[index], spline_points_xz[index]


def distance_along_straight_track(point, center_points):
    """
    Computes the distance along a straight track center to the closest center point,
    returning the result in meters.

    Args:
        point (numpy.ndarray): A 3D coordinate (x, y, z) in meters.
        center_points (numpy.ndarray): A (N, 3) array representing track center points in meters.

    Returns:
        tuple:
            - float: The cumulative distance along the track to the closest center point (in meters).
            - numpy.ndarray: The closest track center point.
    """
    center_points_xz = center_points[:, [0, 2]]
    point_xz = point[[0, 2]]

    tck, _ = splprep(center_points_xz.T, s=0)
    num_samples = 1000
    u_values = np.linspace(0, 1, num_samples)
    spline_points_xz = np.array(splev(u_values, tck)).T

    tree = KDTree(spline_points_xz)
    _, index = tree.query(point_xz)

    segment_lengths = np.linalg.norm(np.diff(spline_points_xz, axis=0), axis=1)
    cumulative_distance = np.cumsum(segment_lengths)
    cumulative_distance = np.insert(cumulative_distance, 0, 0)

    return cumulative_distance[index], spline_points_xz[index]


def get_curve_point_from_angle(radius, angle_degrees):
    """
    Compute the (x, y, z) center position given an angle from the start of the track.

    Parameters:
    - radius (float): Radius of the railway track curve.
    - angle_degrees (float): Angle from the starting position (0 degrees).

    Returns:
    - np.array([x, y, z]): The position in 3D space.
    """
    theta = np.radians(abs(angle_degrees))
    z = radius * np.sin(theta)
    x = radius * (1 - np.cos(theta))
    y = 0

    if angle_degrees < 0:
        x = -x
    
    return np.array([x, y, z])
    

def get_new_position_from_angle(radius, angle_degrees, original_point, curve_points):
    """
    Move the original point along the curve by the specified angle starting from the first point of curve_points,
    preserving the offset of the original point from the closest center point.
    
    Parameters:
    - radius: The radius of the curve at the original point.
    - angle_degrees: The angle (in degrees) to move along the curve.
    - original_point: The (x, y, z) coordinates of the original point.
    - curve_points: A 2D array of center points along the track (each point is (x, y, z)).
    
    Returns:
    - new_position: The new (x, y, z) position of the point on the track after moving by the angle.
    """
    closest_center = find_closest_center_point(original_point, curve_points, plane='xz')
    
    offset = original_point - closest_center
    
    start_point = curve_points[0]
    
    calculated_curve_point = get_curve_point_from_angle(radius, angle_degrees)
    new_x = start_point[0] + calculated_curve_point[0]
    new_z = start_point[2] + calculated_curve_point[2]
    
    new_position = np.array([new_x, original_point[1], new_z]) + offset
    
    return new_position


def get_new_position_from_trackcenter(signed_distance, original_point, center_points):
    """
    Compute the new (x, y, z) position of a point given a new distance from the closest track center.

    Args:
        signed_distance (float): The signed lateral distance from the track center.
        original_point (numpy.ndarray): The original (x, y, z) coordinate of the point.
        center_points (numpy.ndarray): The track center points (N, 3).

    Returns:
        np.array([x, y, z]): The new transformed position in 3D space.
    """
    closest_center = find_closest_center_point(original_point, center_points, plane="xz")

    tck, _ = splprep(center_points.T, s=0)
    num_samples = 1000
    u_values = np.linspace(0, 1, num_samples)
    spline_points = np.array(splev(u_values, tck)).T

    tree = KDTree(spline_points)
    _, index = tree.query(closest_center)

    if index < len(spline_points) - 1:
        tangent_vector = spline_points[index + 1] - spline_points[index]
    else:
        tangent_vector = spline_points[index] - spline_points[index - 1]
    
    tangent_vector[1] = 0
    tangent_vector /= np.linalg.norm(tangent_vector)

    lateral_vector = np.array([-tangent_vector[2], 0, tangent_vector[0]])

    new_position = closest_center + signed_distance * lateral_vector
    return new_position


def get_uv_point_idxs(sfile_lines):
    """
    Extracts UV point indices from a list of shape file lines.

    Args:
        sfile_lines (list of str): The lines from an shape file.

    Returns:
        dict: A dictionary mapping point indices (int) to UV point indices (int).
    """
    uv_point_idxs = {}

    for line_idx in range(0, len(sfile_lines)):
        sfile_line = sfile_lines[line_idx]
        if 'vertex (' in sfile_line.lower():
            parts = "".join(sfile_lines[line_idx : line_idx + 2]).split(" ")
            uv_point_idxs[int(parts[3])] = int(parts[9])

    return uv_point_idxs


def get_uv_point_value(sfile_lines, uv_point_idx):
    """
    Retrieves the UV coordinates for a given UV point index.

    Args:
        sfile_lines (list of str): The lines from an S-file.
        uv_point_idx (int): The index of the UV point.

    Returns:
        tuple or None: A tuple (float, float) representing the U and V coordinates, 
                       or None if the index is not found.
    """
    current_uv_point_idx = 0

    for line_idx in range(0, len(sfile_lines)):
        sfile_line = sfile_lines[line_idx]
        if 'uv_point (' in sfile_line.lower():
            if current_uv_point_idx == uv_point_idx:
                parts = sfile_line.split(" ")
                return float(parts[2]), float(parts[3]),
            current_uv_point_idx += 1

    return None


def set_uv_point_value(sfile_lines, uv_point_idx, u_value, v_value):
    """
    Updates the U and V coordinate values for a given UV point index.

    Args:
        sfile_lines (list of str): The lines from an S-file.
        uv_point_idx (int): The index of the UV point to update.
        u_value (float): The new U coordinate value.
        v_value (float): The new V coordinate value.
    """
    current_uv_point_idx = 0

    for line_idx in range(0, len(sfile_lines)):
        sfile_line = sfile_lines[line_idx]
        if 'uv_point (' in sfile_line.lower():
            if current_uv_point_idx == uv_point_idx:
                parts = sfile_line.split(" ")
                parts[2] = str(u_value)
                parts[3] = str(v_value)
                sfile_line = " ".join(parts)
                sfile_lines[line_idx] = sfile_line
                break
            current_uv_point_idx += 1


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
    vertices_map = []

    prim_state_names = get_prim_state_names(sfile_lines)

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


def get_prim_state_names(sfile_lines):
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
