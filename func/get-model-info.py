# get model's information
# including vertices/faces/uv-mapping count and file size of texture images.

import bpy
import os

vertices_count = 0
polygons_count = 0
uv_count = 0

textures = []
textures_size = 0 # in bytes

for obj in bpy.data.objects:
    vertices_count += len(obj.data.vertices)
    polygons_count += len(obj.data.polygons)

    for uv_map in obj.data.uv_layers:
        uv_count += len(uv_map.data)

print("vertices_count: ", vertices_count)
print("polygons_count: ", polygons_count)
print("uv_count: ", uv_count)

for image in bpy.data.images:
    if image.filepath != '':
        file_size = os.path.getsize(image.filepath) # in bytes
        textures_size += file_size
        textures.append({'path': image.filepath, 'file_size': file_size, 'width': image.size[0], 'height': image.size[1]})

print("all textures: \n", str(textures))
print("total texture size(bytes): \n", str(textures_size))
    