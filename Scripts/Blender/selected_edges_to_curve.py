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

def selected_edges_to_curve(obj):
    """
    Create a polyline curve from the selected edges of a mesh.

    Traverses connected selected edges to determine vertex order and
    generates a new Curve object with a POLY spline matching the edge path.

    Args:
        obj (bpy.types.Object): Mesh object containing selected edges.

    Notes:
        - The mesh must have edges selected in Edit Mode.
        - If the selection contains multiple disconnected edge chains,
          only the first traversed chain will be converted.
        - The resulting curve uses a POLY spline, preserving sharp
          linear segments between vertices.
    """
    if obj.type != 'MESH':
        print("Active object is not a mesh.")
        return
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    edges = [e for e in bm.edges if e.select]
    if not edges:
        print("No edges selected!")
        return
    adjacency = {}
    for e in edges:
        v1, v2 = e.verts
        adjacency.setdefault(v1, []).append(v2)
        adjacency.setdefault(v2, []).append(v1)
    endpoints = [v for v, nbrs in adjacency.items() if len(nbrs) == 1]
    if endpoints:
        start_vert = endpoints[0]
    else:
        start_vert = edges[0].verts[0]
    ordered_verts = []
    visited = set()
    current = start_vert
    prev = None
    while current:
        ordered_verts.append(current)
        visited.add(current)
        neighbors = [v for v in adjacency[current] if v != prev and v not in visited]
        prev, current = current, neighbors[0] if neighbors else None
    curve_data = bpy.data.curves.new("EdgeCurve", type='CURVE')
    curve_data.dimensions = '3D'
    spline = curve_data.splines.new('POLY')
    spline.points.add(len(ordered_verts)-1)
    for i, v in enumerate(ordered_verts):
        spline.points[i].co = (*v.co, 1.0)
    curve_obj = bpy.data.objects.new("EdgeCurve", curve_data)
    bpy.context.collection.objects.link(curve_obj)
    curve_obj.location = obj.location
    bpy.ops.object.mode_set(mode='OBJECT')
    print("Curve created successfully!")


selected_edges_to_curve(bpy.context.active_object)
