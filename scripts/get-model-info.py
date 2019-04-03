# get model's information
# including vertices/faces/uv-mapping count and file size of texture images.

import bpy
import os
import math

# attribute size per element(vertex/polygon) in bytes
VERTEX_SIZE = 12 # float(32) x 3
POLYGON_SIZE = 12 # int(32) x 3
NORMAL_SIZE = 12 # float(32) x 3
UV_SIZE = 8 # float(32) x 2
COLOR_SIZE = 16 # float(32) x 4(RGBA)
TANGENT_SZIE = 16 # float(32) x 4(XYZW)

LEVEL_MAX = 5

vertices_count = 0
polygons_count = 0
uv_count = 0

textures = []
textures_size = 0 # in bytes
geometry_size = None # in bytes

for obj in bpy.data.objects:
    if obj.type == "MESH":
        vertices_count += len(obj.data.vertices)
        polygons_count += len(obj.data.polygons)

for uv_map in obj.data.uv_layers:
    uv_count += len(uv_map.data)

print("vertices_count: ", vertices_count)
print("polygons_count: ", polygons_count)
print("uv_count: ", uv_count)

for image in bpy.data.images:
    if (image.filepath != '') and (image.type == 'IMAGE'):
        if os.path.exists(image.filepath):
            file_size = os.path.getsize(image.filepath) # in bytes
            textures_size += file_size
            textures.append({'path': image.filepath, 'file_size': file_size, 'width': image.size[0], 'height': image.size[1]})

print("all textures: \n", str(textures))
print("total texture size(bytes): \n", str(textures_size))

geometry_size = vertices_count * (VERTEX_SIZE + TANGENT_SZIE + COLOR_SIZE) + \
    polygons_count * POLYGON_SIZE + \
    polygons_count * 3 * NORMAL_SIZE + \
    uv_count * UV_SIZE 

print("expected geometry size: \n", str(geometry_size))

# calculate tiling level
total_size_mb = (textures_size + geometry_size) / (1024*1024)
level = math.ceil(math.log(total_size_mb, 4))

if (level < 0):
    level = 0

if (level > LEVEL_MAX):
    level = LEVEL_MAX

print("proper tiling level: \n", str(level))