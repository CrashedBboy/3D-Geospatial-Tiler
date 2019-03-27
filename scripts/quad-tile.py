# split 3d model into quad-tree tiles
# assume there's only one mesh obj in the scene
# about quad-tree model structure, see: https://cesium.com/blog/2015/04/07/quadtree-cheatseet/

import bpy
import bmesh
import math

target = None

x_min, x_max = math.inf, (-1) * math.inf
y_min, y_max = math.inf, (-1) * math.inf

# get target mesh object, use the first found mesh as target
for obj in bpy.data.objects:
    if obj.type == "MESH":
        target = obj
        bpy.context.view_layer.objects.active = obj
        break

# visit all vertices, get coordinate range in xy-plane and center position(x,y)
if target:
    for v in target.data.vertices:
        if v.co.x < x_min:
            x_min = v.co.x
        elif v.co.x > x_max:
            x_max = v.co.x
        if v.co.y < y_min:
            y_min = v.co.y
        elif v.co.y > y_max:
            y_max = v.co.y
    print("boundry x:", x_min, "-", x_max, ", y:", y_min, "-", y_max)
    center = [(x_min+x_max)/2, (y_min+y_max)/2]
    print("tiling center: (", center[0], ", ", center[1])
else:
    print("no mesh object found")

'''
split model into 4 tiles based on x,y coordinate of vertices.
tile naming format: tile_<x>_<y>

visulization:

---------------------------
|            |            |
|  tile_0_0  |  tile_0_1  |
|            |            |
|-------------------------|
|            |            |
|  tile_1_0  |  tile_1_1  |
|            |            |
|-------------------------|

'''

# select polygons and separate them from original object
if target:
    tile_0_0_vertices = [] # tile 2
    tile_0_1_vertices = [] # tile 0
    tile_1_0_vertices = [] # tile 3
    tile_1_1_vertices = [] # tile 1
    # catergorize vertices
    for v in target.data.vertices:
        if v.co.x >= center[0] and v.co.y >= center[1]:
            tile_0_1_vertices.append(v.index)
        if v.co.x < center[0] and v.co.y >= center[1]:
            tile_0_0_vertices.append(v.index)
        if v.co.x < center[0] and v.co.y < center[1]:
            tile_1_0_vertices.append(v.index)
        if v.co.x >= center[0] and v.co.y < center[1]:
            tile_1_1_vertices.append(v.index)
    tile_0_0_polygons = [] # tile 2
    tile_0_1_polygons = [] # tile 0
    tile_1_0_polygons = [] # tile 3
    tile_1_1_polygons = [] # tile 1
    # catergorize polygons
    for p in target.data.polygons:
        tile = 3 # which tile this polygon belongs to
        for pv in p.vertices:
            if pv in tile_0_0_vertices:
                tile = min(tile, 2)
                continue
            elif pv in tile_0_1_vertices:
                tile = min(tile, 0)
                continue
            elif pv in tile_1_0_vertices:
                tile = min(tile, 3)
                continue
            elif pv in tile_1_1_vertices:
                tile = min(tile, 1)
        if tile == 0:
            tile_0_1_polygons.append(p.index)
            continue
        elif tile == 1:
            tile_1_1_polygons.append(p.index)
            continue
        elif tile == 2:
            tile_0_0_polygons.append(p.index)
            continue
        elif tile == 3:
            tile_1_0_polygons.append(p.index)
    tiles_polygons = [tile_0_0_polygons, tile_0_1_polygons, tile_1_0_polygons, tile_1_1_polygons]
    tiles_names = ['tile_0_0', 'tile_0_1', 'tile_1_0', 'tile_1_1']
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(target.data)
    for name, polygons in zip(tiles_names, tiles_polygons):
        print(len(polygons))
        bpy.ops.mesh.select_all(action='DESELECT')
        selected = False
        for face in bm.faces:
            if face.index in polygons:
                if not selected:
                    selected = True
                face.select_set(True)
        bmesh.update_edit_mesh(target.data, True)
        if (selected):
            bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
