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

# TODO: UV mapping + split materials

RWALL_CURVE_NAME = "EdgeCurve"

RWALL_GUARDRAIL_PROFILE = [
    (-0.1, 0.34, 0.0),
    (-0.1, 1.33, 0.0),
    (-0.2, 1.33, 0.0),
    (-0.2, 0.34, 0.0),
    (-0.1, 0.34, 0.0),
]

def tangent_at(points, i):
    """
    Computes a tangent vector along a polyline.

    Args:
        points (list[Vector]): List of spline points.
        i (int): Index of the current point.

    Returns:
        Vector: Normalized tangent direction.
    """
    if i == 0:
        return (points[1] - points[0]).normalized()
    elif i == len(points)-1:
        return (points[-1] - points[-2]).normalized()
    else:
        return (points[i+1] - points[i-1]).normalized()


def sweep_profile_along_curve(curve_obj, profile):
    """
    Generates a guardrail mesh by sweeping a profile along a curve.

    Args:
        curve_obj (bpy.types.Object): Curve object defining the sweep path.
        profile (list[tuple]): Cross-section profile coordinates.

    Returns:
        bpy.types.Object: Generated guardrail mesh object.

    Notes:
        - Profile is aligned to the spline tangent.
        - Side faces and end caps are generated.
        - Geometry is cleaned and normals recalculated.
    """
    spline = curve_obj.data.splines[0]
    mesh = bpy.data.meshes.new("GuardRail")
    guardrail_obj = bpy.data.objects.new("GuardRail", mesh)
    bpy.context.collection.objects.link(guardrail_obj)
    bm = bmesh.new()
    vertices_along_spline = []
    points_3d = [Vector(p.co.xyz) for p in spline.points]
    for i, pt in enumerate(points_3d):
        row = []
        tangent = tangent_at(points_3d, i)
        z_axis = tangent
        up = Vector((0,0,1))
        if abs(z_axis.dot(up)) > 0.999:
            up = Vector((0,1,0))
        x_axis = up.cross(z_axis).normalized()
        y_axis = z_axis.cross(x_axis).normalized()
        rot = Matrix((x_axis, y_axis, z_axis)).transposed()
        for px, py, v in profile:
            local = Vector((px, py, 0))
            vert = bm.verts.new(pt + rot @ local)
            row.append(vert)
        vertices_along_spline.append(row)
    bm.verts.ensure_lookup_table()
    for i in range(len(vertices_along_spline)-1):
        loop1 = vertices_along_spline[i]
        loop2 = vertices_along_spline[i+1]
        n = len(loop1)
        for j in range(n-1):
            bm.faces.new([loop1[j], loop2[j], loop2[j+1], loop1[j+1]])
    bm.faces.new(vertices_along_spline[0])
    bm.faces.new(list(reversed(vertices_along_spline[-1])))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return guardrail_obj


def build_guardrail():
    """
    Main execution function that generates the guardrail mesh from the curve.
    """
    curve_obj = bpy.data.objects[RWALL_CURVE_NAME]
    sweep_profile_along_curve(curve_obj, RWALL_GUARDRAIL_PROFILE)


build_guardrail()