"""
Copyright (C) 2026 Peter Grønbæk Andersen <peter@grnbk.io>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import bpy
import bmesh
from mathutils import Vector


LOOP_A_COORDS = [
    Vector((0, 0, 0)),
    Vector((1, 0, 0)),
    Vector((2, 0, 0)),
]

LOOP_B_COORDS = [
    Vector((0, 1, 0)),
    Vector((0.8, 1, 0)),
    Vector((1.6, 1, 0)),
    Vector((2.4, 1, 0)),
    Vector((3, 1, 0)),
    Vector((3.2, 1, 0)),
]

TILE_U_PER_METER = 1.0
TILE_V_PER_METER = 1.0


def cumulative_distances(verts):
    """
    Computes cumulative distances along a list of vertices.

    Args:
        verts (list[bmesh.types.BMVert]): Vertices forming a polyline.

    Returns:
        list[float]: Cumulative distance values along the vertex chain.
    """
    dists = [0.0]
    for i in range(1, len(verts)):
        dists.append(dists[-1] + (verts[i].co - verts[i-1].co).length)
    return dists


def stitch_loops(loop_a_coords, loop_b_coords, tile_u_per_meter, tile_v_per_meter):
    """
    Creates a stitched mesh surface between two vertex loops with UV mapping.

    Args:
        loop_a_coords (list[Vector]): Coordinates of the first edge loop.
        loop_b_coords (list[Vector]): Coordinates of the second edge loop.
        tile_u_per_meter (float): Texture repeat rate along the stitched direction.
        tile_v_per_meter (float): Texture repeat rate across the stitch.

    Returns:
        bpy.types.Object: Generated stitched mesh object.

    Notes:
        - Handles loops with different vertex counts.
        - Faces are generated progressively along both edge chains.
        - UV coordinates follow cumulative edge distance.
    """
    mesh = bpy.data.meshes.new("stitch_mesh")
    obj = bpy.data.objects.new("StitchObject", mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()
    verts_a = [bm.verts.new(v) for v in loop_a_coords]
    verts_b = [bm.verts.new(v) for v in loop_b_coords]
    bm.verts.ensure_lookup_table()
    dists_a = cumulative_distances(verts_a)
    dists_b = cumulative_distances(verts_b)
    total_len_a = dists_a[-1]
    total_len_b = dists_b[-1]
    i = 0
    j = 0
    while i < len(verts_a) - 1 and j < len(verts_b) - 1:
        a0 = verts_a[i]
        a1 = verts_a[i+1]
        b0 = verts_b[j]
        b1 = verts_b[j+1]
        da = dists_a[i+1] - dists_a[i]
        db = dists_b[j+1] - dists_b[j]
        if da / total_len_a < db / total_len_b:
            bm.faces.new([a0, b0, b1, a1])
            i += 1
        elif da / total_len_a > db / total_len_b:
            bm.faces.new([a0, b0, b1, a1])
            j += 1
        else:
            bm.faces.new([a0, b0, b1, a1])
            i += 1
            j += 1
    uv_layer = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for l in f.loops:
            v = l.vert
            if v in verts_a:
                idx = verts_a.index(v)
                u = dists_a[idx] * tile_u_per_meter
                v_coord = (loop_b_coords[0].y - loop_a_coords[0].y) * tile_v_per_meter
            else:
                idx = verts_b.index(v)
                u = dists_b[idx] * tile_u_per_meter
                v_coord = 0.0
            l[uv_layer].uv = (u, v_coord)
    bm.to_mesh(mesh)
    bm.free()
    return obj


def build_stitch_mesh():
    """
    Main execution function that creates the stitched mesh.
    """
    stitch_loops(LOOP_A_COORDS, LOOP_B_COORDS, TILE_U_PER_METER, TILE_V_PER_METER)


build_stitch_mesh()