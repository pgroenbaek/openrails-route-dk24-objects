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
from mathutils import Vector, Matrix

curve_obj = bpy.data.objects['Tommerup, Spor 3']
spline = curve_obj.data.splines[0]

profile = [
    (0.0, 0.0, 0.0), # X,Y,V
    (0.0, 0.6, 1.0),
    (0.3, 0.6, 1.0),
    (0.3, 0.3, 0.5),
    (0.6, 0.3, 0.5),
    (0.6, 0.0, 0.0),
]

repeats_per_meter = 2.0 # Mumber of texture repeats per meter along the spline

mesh = bpy.data.meshes.new("spline_mesh")
obj = bpy.data.objects.new("SplineObject", mesh)
bpy.context.collection.objects.link(obj)

bm = bmesh.new()

def tangent_at(points, i):
    if i == 0:
        return (points[1] - points[0]).normalized()
    elif i == len(points)-1:
        return (points[-1] - points[-2]).normalized()
    else:
        return (points[i+1] - points[i-1]).normalized()

vertices_along_spline = []
points_3d = [Vector(p.co.xyz) for p in spline.points]
v_coords_along_spline = []

for i, pt in enumerate(points_3d):
    row = []
    row_v = []
    tangent = tangent_at(points_3d, i)
    z_axis = tangent
    up = Vector((0, 0, 1))
    if abs(z_axis.dot(up)) > 0.999:
        up = Vector((0, 1, 0))
    x_axis = up.cross(z_axis).normalized()
    y_axis = z_axis.cross(x_axis).normalized()
    rot = Matrix((x_axis, y_axis, z_axis)).transposed()
    for px, py, v in profile:
        local = Vector((px, py, 0))
        vert = bm.verts.new(pt + rot @ local)
        row.append(vert)
        row_v.append(v)
    vertices_along_spline.append(row)
    v_coords_along_spline.append(row_v)

bm.verts.ensure_lookup_table()

for i in range(len(vertices_along_spline)-1):
    loop1 = vertices_along_spline[i]
    loop2 = vertices_along_spline[i+1]
    n = len(loop1)
    for j in range(n-1):
        bm.faces.new([loop1[j], loop2[j], loop2[j+1], loop1[j+1]])

start_loop = vertices_along_spline[0]
end_loop = vertices_along_spline[-1]
bm.faces.new(start_loop)
bm.faces.new(reversed(end_loop))

bm.to_mesh(mesh)
bm.free()

if not mesh.uv_layers:
    mesh.uv_layers.new(name="UVMap")

uv_layer = mesh.uv_layers.active.data

cumulative_lengths = [0.0]
for i in range(1, len(points_3d)):
    seg_len = (points_3d[i] - points_3d[i-1]).length
    cumulative_lengths.append(cumulative_lengths[-1] + seg_len)

profile_len = len(profile)

for f_idx, face in enumerate(mesh.polygons):
    for l_idx, loop_idx in enumerate(face.loop_indices):
        vert_idx = mesh.loops[loop_idx].vertex_index
        profile_idx = vert_idx % profile_len
        spline_idx = vert_idx // profile_len
        v_coord = v_coords_along_spline[spline_idx][profile_idx]
        u_coord = cumulative_lengths[spline_idx] * repeats_per_meter
        uv_layer[loop_idx].uv = (u_coord, v_coord)
