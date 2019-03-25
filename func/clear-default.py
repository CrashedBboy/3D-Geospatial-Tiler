# delete every object (including camera and light source) in the scene

import bpy

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=True)