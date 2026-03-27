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


EMBANKMENT_OBJECT_NAME = "Embankment"
UNDERPASS_CURVE_NAME = "Underpass"

WALL_THICKNESS = 0.7

CUT_PROFILE = [
    (-3.7 - WALL_THICKNESS, -10.0 - WALL_THICKNESS),
    (-3.7 - WALL_THICKNESS, 7.9 + WALL_THICKNESS),
    (3.7 + WALL_THICKNESS, 7.9 + WALL_THICKNESS),
    (3.7 + WALL_THICKNESS, -10.0 - WALL_THICKNESS),
]

SUBDIVIDE_CUTS = 1


def duplicate_object(obj):
    """
    Creates a duplicate of a Blender object including its mesh data.

    Args:
        obj (bpy.types.Object): Object to duplicate.

    Returns:
        bpy.types.Object: Newly created duplicate object.

    Notes:
        - The duplicate mesh data is independent from the original.
        - The object is linked to the current active collection.
    """
    duplicate = obj.copy()
    duplicate.data = obj.data.copy()
    duplicate.name = obj.name + "_original"
    bpy.context.collection.objects.link(duplicate)
    print("Duplicated original embankment:", duplicate.name)
    return duplicate


def subdivide_mesh(obj, cuts):
    """
    Subdivides all edges of a mesh object to improve boolean stability.

    Args:
        obj (bpy.types.Object): Mesh object to subdivide.
        cuts (int): Number of subdivision cuts.
    """
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.subdivide_edges(
        bm,
        edges=bm.edges,
        cuts=cuts,
        use_grid_fill=True
    )
    bm.to_mesh(me)
    bm.free()


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


def create_tunnel_cutter(curve_obj, cut_profile):
    """
    Generates a cutter mesh by extruding a profile along a curve.

    Args:
        curve_obj (bpy.types.Object): Curve object defining the path.
        cut_profile (list[tuple]): 2D profile coordinates.

    Returns:
        bpy.types.Object: The generated cutter mesh object.

    Notes:
        - Profile is aligned to the spline tangent at each point.
        - Resulting geometry is fully closed and suitable for boolean operations.
    """
    mesh = bpy.data.meshes.new("TunnelCutter")
    cutter_obj = bpy.data.objects.new("TunnelCutter", mesh)
    bpy.context.collection.objects.link(cutter_obj)
    bm = bmesh.new()
    spline = curve_obj.data.splines[0]
    points_3d = [Vector(p.co.xyz) for p in spline.points]
    vertices_along = []
    for i, pt in enumerate(points_3d):
        tangent = tangent_at(points_3d, i)
        z_axis = tangent
        up = Vector((0,0,1))
        if abs(z_axis.dot(up)) > 0.999:
            up = Vector((0,1,0))
        x_axis = up.cross(z_axis).normalized()
        y_axis = z_axis.cross(x_axis).normalized()
        rot = Matrix((x_axis, y_axis, z_axis)).transposed()
        row = []
        for px, py in cut_profile:
            local = Vector((px, py, 0))
            vert = bm.verts.new(pt + rot @ local)
            row.append(vert)
        vertices_along.append(row)
    bm.verts.ensure_lookup_table()
    for i in range(len(vertices_along)-1):
        loop1 = vertices_along[i]
        loop2 = vertices_along[i+1]
        for j in range(len(loop1)):
            v1 = loop1[j]
            v2 = loop1[(j+1) % len(loop1)]
            v3 = loop2[(j+1) % len(loop2)]
            v4 = loop2[j]
            bm.faces.new([v1, v2, v3, v4])
    bm.faces.new(vertices_along[0])
    bm.faces.new(list(reversed(vertices_along[-1])))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return cutter_obj


def triangulate_mesh(obj):
    """
    Triangulates a mesh to improve boolean solver stability.

    Args:
        obj (bpy.types.Object): Mesh object to triangulate.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def apply_boolean_cut(target_obj, cutter_obj):
    """
    Applies a boolean difference operation using a cutter object.

    Args:
        target_obj (bpy.types.Object): Object to cut.
        cutter_obj (bpy.types.Object): Cutter mesh.
    """
    bool_mod = target_obj.modifiers.new("EmbankmentCut", 'BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = cutter_obj
    bool_mod.solver = 'EXACT'
    bool_mod.use_self = True
    bpy.context.view_layer.objects.active = target_obj
    bpy.ops.object.modifier_apply(modifier="EmbankmentCut")


def build_underpass_cut():
    """
    Main pipeline that builds and applies the underpass boolean cut.

    Steps:
        1. Duplicate the original embankment mesh.
        2. Subdivide the mesh to improve boolean stability.
        3. Generate a cutter mesh from the flyover curve.
        4. Triangulate the cutter mesh.
        5. Apply the boolean difference operation.
    """
    embankment_obj = bpy.data.objects[EMBANKMENT_OBJECT_NAME]
    flyover_curve = bpy.data.objects[UNDERPASS_CURVE_NAME]
    duplicate_object(embankment_obj)
    subdivide_mesh(embankment_obj, SUBDIVIDE_CUTS)
    cutter_obj = create_tunnel_cutter(flyover_curve, CUT_PROFILE)
    triangulate_mesh(cutter_obj)
    apply_boolean_cut(embankment_obj, cutter_obj)


build_underpass_cut()