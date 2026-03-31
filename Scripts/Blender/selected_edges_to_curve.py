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
    Converts selected edges of a mesh object into a 3D curve object.

    Args:
        obj (bpy.types.Object): The active mesh object with selected edges.

    Notes:
        - The function works only if the active object is a mesh.
        - Traverses connected selected edges to form continuous chains.
        - Each chain becomes a separate spline in the new curve.
        - The resulting curve is linked to the current collection and named "EdgeCurve".
        - Preserves the original object location.
    """
    if obj.type != 'MESH':
        print("Active object is not a mesh.")
        return
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    edges = [e for e in bm.edges if e.select]
    if not edges:
        print("No edges selected!")
        bpy.ops.object.mode_set(mode='OBJECT')
        return
    adjacency = {}
    for e in edges:
        v1, v2 = e.verts
        adjacency.setdefault(v1, []).append(v2)
        adjacency.setdefault(v2, []).append(v1)
    visited = set()
    def traverse_chain(start):
        chain = []
        stack = [(start, None)]
        while stack:
            v, prev = stack.pop()
            if v in visited:
                continue
            visited.add(v)
            chain.append(v)
            neighbors = [n for n in adjacency.get(v, []) if n != prev and n not in visited]
            if neighbors:
                stack.append((neighbors[0], v))
        return chain
    endpoints = [v for v, nbrs in adjacency.items() if len(nbrs) == 1]
    chains = []
    for ep in endpoints:
        if ep not in visited:
            chains.append(traverse_chain(ep))
    for v in adjacency:
        if v not in visited:
            chains.append(traverse_chain(v))
    curve_data = bpy.data.curves.new("EdgeCurve", type='CURVE')
    curve_data.dimensions = '3D'
    for chain in chains:
        spline = curve_data.splines.new('POLY')
        spline.points.add(len(chain)-1)
        for i, v in enumerate(chain):
            spline.points[i].co = (*v.co, 1.0)
    curve_obj = bpy.data.objects.new("EdgeCurve", curve_data)
    bpy.context.collection.objects.link(curve_obj)
    curve_obj.location = obj.location
    bpy.ops.object.mode_set(mode='OBJECT')
    print("Curve created successfully!")

selected_edges_to_curve(bpy.context.active_object)