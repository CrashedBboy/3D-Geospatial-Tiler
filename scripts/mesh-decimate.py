# reduce number of meshes in 3d model

import bpy

MODE = 'DECIMATE'
MODIFIER_NAME = 'decimator'
RATIO = 0.75


mesh_list = []

for obj in bpy.data.objects:
    if obj.type == "MESH":
        mesh_list.append(obj)

for obj in mesh_list:
    bpy.context.view_layer.objects.active = obj
    modifier = obj.modifiers.new(MODIFIER_NAME, MODE)
    modifier.decimate_type = 'COLLAPSE'
    modifier.ratio = 0.5
    modifier.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier=MODIFIER_NAME)

