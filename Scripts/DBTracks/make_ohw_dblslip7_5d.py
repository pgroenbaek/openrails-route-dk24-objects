import os
import numpy as np
import trackshapeutils as tsu

def make_matrix(m11, m12, m13, m21, m22, m23, m31, m32, m33, m41, m42, m43):
    return np.array([
        [m11, m12, m13, m41],
        [m21, m22, m23, m42],
        [m31, m32, m33, m43],
        [0.0, 0.0, 0.0, 1.0]
    ])

matrices = {
    "T4_L450M1_F1WIRE25W01": make_matrix(
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
        0.0, 0.0, 1.0,
        0.0, 6.2, -10.0
    ),
    "T4_L450M1_F1WIRE25W02": make_matrix(
        0.991, 0.0, -0.131,
        0.0, 1.0, 0.0,
        0.131, 0.0, 0.991,
        1.632, 6.2, -9.893
    ),
    "SIN_T_E": make_matrix(
        -1.0, 0.0, 0.0,
        0.0, 0.0, -1.0,
        0.0, -1.0, 0.0,
        0.0, 0.0, 2.5
    )
}

def remap_point(p, M):
    p = np.array([p.x, p.y, p.z, 1.0])
    p_new = M @ p
    return p_new[:3] / p_new[3]

def remap_normal(n, M):
    linear = M[:3, :3]
    normal_matrix = np.linalg.inv(linear).T
    n = np.array([n.vec_x, n.vec_y, n.vec_z])
    n_new = normal_matrix @ n
    n_new /= np.linalg.norm(n_new)
    return n_new

if __name__ == "__main__":
    shape_load_path = "../../../../Content/PGA DK24/GLOBAL/SHAPES"
    shape_processed_path = "./Processed/OhwDblSlip7_5d"
    ffeditc_path = "./ffeditc_unicode.exe"
    cwire_shape = "DB2f_A1tDblSlip7_5d.s"
    match_shapes = ["DB2_A1tDblSlip7_5d.s", "DB3_A1tDblSlip7_5d.s", "DB2_A1tDKW7_5d.s", "DB3_A1tDKW7_5d.s"]
    ignore_shapes = []
    
    os.makedirs(shape_processed_path, exist_ok=True)

    shape_names = tsu.find_directory_files(shape_load_path, match_shapes, ignore_shapes)

    original_cwire_sfile = tsu.load_shape(cwire_shape, shape_load_path)
    cwire_sfile = original_cwire_sfile.copy(new_filename=cwire_shape.replace("DB2f_", "cwire_"), new_directory=shape_processed_path)
    cwire_sfile.decompress(ffeditc_path)

    for idx, sfile_name in enumerate(shape_names):
        print(f"Shape {idx + 1} of {len(shape_names)}...")
        new_sfile_name = sfile_name.replace("DB2_", "DB2f_")
        new_sfile_name = new_sfile_name.replace("DB3_", "DB3f_")

        sfile = tsu.load_shape(sfile_name, shape_load_path)
        new_sfile = sfile.copy(new_filename=new_sfile_name, new_directory=shape_processed_path)
        new_sfile.decompress(ffeditc_path)

        lod_dlevel = 500
        subobject_idx = 0
        prim_states = new_sfile.get_prim_states_by_name("Material_#1")

        cwire_lod_dlevel = 200
        cwire_subobject_idx = 3
        mt_cwire_prim_states = cwire_sfile.get_prim_states_by_name("mt_cwire")
        
        for mt_cwire in mt_cwire_prim_states:
            mt_cwire_vertices = cwire_sfile.get_vertices_by_prim_state(cwire_lod_dlevel, mt_cwire)
            mt_cwire_indexed_trilists = cwire_sfile.get_indexed_trilists_in_subobject_by_prim_state(cwire_lod_dlevel, cwire_subobject_idx, mt_cwire)
            indexed_trilists = new_sfile.get_indexed_trilists_in_subobject_by_prim_state(lod_dlevel, subobject_idx, prim_states[0])

            # Re-map points and normals from the matrices in Norbert Rieger's shape to fit the Material_#1 matrix.
            if mt_cwire.idx == 0:
                print(f"\tProcessing: T4_L450M1_F1WIRE25W01")
                M_old = matrices["T4_L450M1_F1WIRE25W01"]
            elif mt_cwire.idx == 1:
                print(f"\tProcessing: T4_L450M1_F1WIRE25W02")
                M_old = matrices["T4_L450M1_F1WIRE25W02"]
            
            M_new = matrices["SIN_T_E"]
            M_new_inv = np.linalg.inv(M_new)
            M_transform = M_new_inv @ M_old

            processed_point_idxs = set()
            processed_normal_idxs = set()

            for v in mt_cwire_vertices:
                if v.point_idx not in processed_point_idxs:
                    x, y, z = remap_point(v.point, M_transform)
                    v.point.x = x
                    v.point.y = y
                    v.point.z = z
                    processed_point_idxs.add(v.point_idx)

                if v.normal_idx not in processed_normal_idxs:
                    vec_x, vec_y, vec_z = remap_normal(v.normal, M_transform)
                    v.normal.vec_x = vec_x
                    v.normal.vec_y = vec_y
                    v.normal.vec_z = vec_z
                    processed_normal_idxs.add(v.normal_idx)

            if len(mt_cwire_indexed_trilists) == 0:
                print("No indexed trilist for 'mt_cwire', skipping...")
                continue
            
            if len(indexed_trilists) == 0:
                print("No indexed trilist for 'Material_#1', skipping...")
                continue

            mt_cwire_indexed_trilist = mt_cwire_indexed_trilists[0]
            indexed_trilist = indexed_trilists[0]
            
            new_vertex_lookup = {} # Key is vertex_idx of mt_cwire, value is new_vertex.

            for idx, mt_cwire_vertex in enumerate(mt_cwire_vertices):
                print(f"\tAdding vertex {idx + 1} of {len(mt_cwire_vertices)}", end='\r')
                new_vertex = new_sfile.add_vertex_to_subobject(lod_dlevel, subobject_idx, indexed_trilist, mt_cwire_vertex.point, mt_cwire_vertex.uv_point, mt_cwire_vertex.normal)

                if mt_cwire_vertex.vertex_idx not in new_vertex_lookup:
                    new_vertex_lookup[mt_cwire_vertex.vertex_idx] = new_vertex
            
            print("")

            mt_cwire_triangles = [tuple(mt_cwire_indexed_trilist.vertex_idxs[i : i + 3]) for i in range(0, len(mt_cwire_indexed_trilist.vertex_idxs), 3)]
            mt_cwire_normal_idxs = [tuple(mt_cwire_indexed_trilist.normal_idxs[i : i + 2]) for i in range(0, len(mt_cwire_indexed_trilist.normal_idxs), 2)]

            for idx, (cwire_triangle, cwire_normal_idx) in enumerate(zip(mt_cwire_triangles, mt_cwire_normal_idxs)):
                print(f"\tInserting triangle {idx + 1} of {len(mt_cwire_triangles)}", end='\r')
                vertex1 = new_vertex_lookup[cwire_triangle[0]]
                vertex2 = new_vertex_lookup[cwire_triangle[1]]
                vertex3 = new_vertex_lookup[cwire_triangle[2]]
                new_sfile.insert_triangle_between(indexed_trilist, vertex1, vertex2, vertex3)

                face_normal_idx = indexed_trilist.normal_idxs[-2]
                face_normal = cwire_sfile.get_normal_by_idx(cwire_normal_idx[0])
                vec_x, vec_y, vec_z = remap_normal(face_normal, M_transform)
                face_normal.vec_x = vec_x
                face_normal.vec_y = vec_y
                face_normal.vec_z = vec_z
                new_sfile.set_normal_value(face_normal_idx, face_normal)
            
            print("")
            
        new_sfile.save()
        new_sfile.compress(ffeditc_path)

        sdfile_name = sfile_name.replace(".s", ".sd")
        new_sdfile_name = new_sfile_name.replace(".s", ".sd")

        sdfile = tsu.load_file(sdfile_name, shape_load_path)
        new_sdfile = sdfile.copy(new_filename=new_sdfile_name, new_directory=shape_processed_path)
        new_sdfile.replace_ignorecase(sfile_name, new_sfile_name)
        new_sdfile.save()
