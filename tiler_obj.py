import sys
import os
from os import path
import json

# get current script direcotry
current_dir = os.path.dirname(__file__)

# append current path to blender modules path (in order to import our own module)
if not current_dir in sys.path:
   sys.path.append(current_dir)

# get program setting constants
settings_filepath = path.abspath(path.join(path.dirname(__file__), "settings.json"))

settings = None

with open(settings_filepath, 'r') as reader:
    settings = json.load(reader)

pypi_packages_path = settings['PYPI_PACKAGE_PATH']

if (pypi_packages_path != None):
    
    if not pypi_packages_path in sys.path:
        sys.path.append(pypi_packages_path)

import bpy
import subprocess
import funcs

print("\n---------------------program started---------------------\n")

# clear all default objects in the scene
funcs.clear_default()

IMPORT_MODEL = './models/mountain/mountain.obj'
# IMPORT_MODEL = './models/wood_house/house.obj'
# IMPORT_MODEL = './models/chocolate_farm/choco.obj'

# EXPORT_DIR = './export/choco_from_obj'
# EXPORT_DIR = './export/house'
EXPORT_DIR = './export/mountain_from_obj'

LATITUDE = 25.082977
LONGITUDE = 121.245466
HEIGHT = 10

settings = funcs.get_settings()

absolute_model_path = path.abspath( path.join(current_dir, IMPORT_MODEL) )

absolute_export_directory = path.abspath( path.join(current_dir, EXPORT_DIR) )

# create direcotry for exporting
os.makedirs(absolute_export_directory, exist_ok=True)
os.makedirs(path.join(absolute_export_directory, 'gltf'), exist_ok=True)
os.makedirs(path.join(absolute_export_directory, '3dtiles'), exist_ok=True)

import_result = False
import_result = funcs.import_obj(absolute_model_path, axis_forward="Y", axis_up="Z")

if import_result == False:
    exit()

# join all objects into one
funcs.join_all()

# check texture images size and downscale them (to save memory)
funcs.limit_texture(settings["TEX_MAX_SIZE"])

# create directory to store original textures
original_tex_dir = path.join(absolute_export_directory, 'original_tex')
os.makedirs(original_tex_dir, exist_ok=True)

# export the original texture images
original_textures = []
count = 0
for img in bpy.data.images:
    if (img.type == "IMAGE"):

        name = "Image_" + str(count)
        filename = name + ".jpg"
        count += 1

        # rename image
        img.name = name

        filepath = path.join(original_tex_dir, filename)

        funcs.export_texture(image=img, filepath=filepath)
        original_textures.append(filepath)

# downscale all texture image to size [1,1]
# funcs.minimize_texture()

# export model into glTF format
root_gltf_path = path.join(absolute_export_directory, 'root.glb')

export_result = funcs.export_gltf(filepath=root_gltf_path, format='GLB', yup=False)
if (export_result == False):
    exit()

# export model into OBJ format as root source
root_obj_path = path.join(absolute_export_directory, 'root.obj')

export_result = funcs.export_obj(
    filepath=root_obj_path,
    selected=False,
    axis_forward=settings["AXIS_FORWARD"],
    axis_up=settings["AXIS_UP"]
    )

if (export_result == False):
    exit()

# get size of mesh and textures
level = funcs.get_proper_level(root_gltf_path)

if (level == None):
    exit()

level = 1

all_tiles = []

# generate each level's tile
print("generate each level's tile")
for l in range(0, level+1):

    # clear all objects/uv_maps/images
    funcs.clear_all()

    # reload the root model
    funcs.import_obj(root_obj_path, axis_forward=settings["AXIS_FORWARD"], axis_up=settings["AXIS_UP"])
    root_object = bpy.data.objects[0]

    # decimate mesh
    decimate_percentage = funcs.get_decimate_percentage(l, level)
    print("decimate mesh to", str(decimate_percentage*100)+"%")
    funcs.mesh_decimate(root_object, decimate_percentage)

    # split mesh object into (2 x 2)^n sub-meshes
    tiles = funcs.tile_model(root_object, l, level)
    print("split into", len(tiles), "tiles")

    # minimize all textures
    funcs.minimize_texture()

    count = 0
    for img in bpy.data.images:
        if (img.type == "IMAGE"):

            name = "Image_" + str(count)
            count += 1

            # rename image
            img.name = name

    # export
    for tile in tiles:

        mesh = bpy.data.objects[tile["name"]]
        export_name = 'tile_' + str(tile["level"]) + "_" + str(tile["x"]) + "_" + str(tile["y"])

        # set export destination
        tile_dir = path.join(absolute_export_directory, 'gltf', export_name)
        tile_path = path.join(tile_dir, 'model.gltf')
        os.makedirs(tile_dir, exist_ok=True)

        # store tile's infomation
        all_tiles.append({ "level": tile["level"], "total_level": level, "x": tile["x"], "y": tile["y"], "gltf_path": tile_path })

        # deselect all
        bpy.ops.object.select_all(action='DESELECT')
        mesh.select_set(True)

        # export
        funcs.export_gltf(filepath=tile_path, format='GLTF_SEPARATE', selected=True, yup=False)

# export LOD infomation
print("export LOD data")
lod_data_path = path.join(absolute_export_directory, 'lod.json')
with open(lod_data_path, 'w') as lod_data:  
    json.dump(all_tiles, lod_data)

# get uv mapping data
uv_parser_proc = funcs.parse_uv(lod_data_path=lod_data_path)
print(uv_parser_proc)

if (uv_parser_proc == False) or (uv_parser_proc.returncode == 1):
    print("failed to parse UV mapping data from GLTF model, exit")
    exit()

# refine & compress texture images
for tile in all_tiles:
    funcs.refine_texture(tile, original_textures=original_textures)

# update texture images name in GLTF models
for tile in all_tiles:
    texture_updater_proc = funcs.update_texture(tile)

    if (texture_updater_proc == False)  or (uv_parser_proc.returncode == 1):
        print("failed to update texture image filename for GLTF model, exit")
        exit()

# convert gltf into b3dm & generate 3d tiles
tileset_path = path.join(absolute_export_directory, '3dtiles')
generator_proc = funcs.generate_tree_3d_tiles(input_path=lod_data_path, output_path=tileset_path, latitude=str(LATITUDE), longitude=str(LONGITUDE), height=str(HEIGHT))
print(generator_proc)

if (generator_proc == False) or (generator_proc.returncode == 1):
    print(generator_proc)
    print("failed to generate 3D tileset, exit")
    exit()

print("processing completed")