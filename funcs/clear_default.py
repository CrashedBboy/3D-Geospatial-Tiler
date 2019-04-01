# delete every object (including camera and light source) in the scene

import bpy

def clear_default():
    print("ACTION: clear all default objects(cube, lamp, camera) in the scene.")
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=True)
