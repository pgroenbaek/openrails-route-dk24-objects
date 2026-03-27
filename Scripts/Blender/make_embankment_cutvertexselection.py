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
from mathutils import bvhtree


THRESHOLD = 0.001  # Distance tolerance


def select_vertices_touching_both(original, result, cutter, threshold=THRESHOLD):
    """
    Select vertices in the result mesh that are within `threshold` distance of both
    the original mesh and the cutter mesh.

    Args:
        original (bpy.types.Object): Original mesh before Boolean.
        result (bpy.types.Object): Boolean-modified mesh.
        cutter (bpy.types.Object): Cutter mesh used in Boolean.
        threshold (float, optional): Distance tolerance for selection.

    Returns:
        list[bmesh.types.BMVert]: List of vertices selected in the result mesh.
    """
    bm_orig = bmesh.new()
    bm_orig.from_mesh(original.data)
    bm_orig.verts.ensure_lookup_table()
    bm_orig.faces.ensure_lookup_table()
    bvh_orig = bvhtree.BVHTree.FromBMesh(bm_orig)
    bm_cut = bmesh.new()
    bm_cut.from_mesh(cutter.data)
    bm_cut.verts.ensure_lookup_table()
    bm_cut.faces.ensure_lookup_table()
    bvh_cut = bvhtree.BVHTree.FromBMesh(bm_cut)
    bpy.context.view_layer.objects.active = result
    bpy.ops.object.mode_set(mode='EDIT')
    bm_result = bmesh.from_edit_mesh(result.data)
    bm_result.verts.ensure_lookup_table()
    for v in bm_result.verts:
        v.select = False
    touching_both = []
    for v in bm_result.verts:
        nearest_orig = bvh_orig.find_nearest(v.co)
        nearest_cut = bvh_cut.find_nearest(v.co)
        if (nearest_orig and nearest_orig[3] <= threshold) and (nearest_cut and nearest_cut[3] <= threshold):
            v.select = True
            touching_both.append(v)
    bmesh.update_edit_mesh(result.data)
    bm_orig.free()
    bm_cut.free()
    return touching_both


def main():
    """
    Main execution function to select vertices touching both the original and cutter meshes.
    """
    original = embankment_obj_orig
    result = embankment_obj
    cutter = cutter_obj
    touching = select_vertices_touching_both(original, result, cutter, THRESHOLD)
    print("Vertices touching both the original embankment and cutter:", len(touching))


main()