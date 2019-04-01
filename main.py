import sys
import os

# get current script direcotry
current_dir = os.path.dirname(__file__)

# append current path to blender modules path (in order to import our own module)
if not current_dir in sys.path:
   sys.path.append(current_dir)

import bpy
from os import path
import funcs

print("\n---------------------program started---------------------\n")

# clear all default objects in the scene
funcs.clear_default()

# import model (GLTF for example)
# supported formats: OBJ, FBX, DAE, GLTF

IMPORT_MODEL = './models/mountain-gltf/model.gltf'
IMPORT_FORMAT = 'GLTF'
# IMPORT_MODEL = './models/mountain/mountain.obj'
# IMPORT_FORMAT = 'OBJ'
import_result = None

absolute_model_path = path.abspath( path.join(current_dir, IMPORT_MODEL) )

if (IMPORT_FORMAT == 'GLTF'):
    import_result = funcs.import_gltf(absolute_model_path)
elif (IMPORT_FORMAT == 'OBJ'):
    import_result = funcs.import_obj(absolute_model_path)

if import_result == None:
    exit()

# join all objects into one
funcs.join_all()

# triangulate
funcs.triangulate()

# export model into GLTF format as root source

# get size of mesh and textures

# generate each level's tile

# decimate mesh

# split mesh object into 2 x 2 sub-mesh

# export 

# refine & compress texture images

# convert gltf into b3dm & generate 3d tiles
