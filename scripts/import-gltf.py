# import 3d models in gltf format
# note: Blender under version 2.8 does not support importing gltf by default

import bpy
import os

FILEPATH = 'C:\\Users\\CrashedBboy\\Projects\\blender-3d-tiler\\models\\mountain-gltf\\model.gltf'

bpy.ops.import_scene.gltf(filepath=FILEPATH, import_pack_images=True, import_shading='NORMALS')
