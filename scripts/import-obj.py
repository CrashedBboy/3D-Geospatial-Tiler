# import a model in OBJ format into blender

import bpy
import os

obj = "../../models/mountain/mountain.obj"

obj_abs_path = os.path.abspath(os.path.join(__file__, obj))

bpy.ops.import_scene.obj(filepath = obj_abs_path)