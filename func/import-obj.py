# import a model in OBJ format into blender

import bpy
import os

obj_path = "C:\\Users\\CrashedBboy\\Downloads\\blender-project\\model\\wulin_model_m100\\wulin.obj"

bpy.ops.import_scene.obj(filepath = obj_path)