# triangulate meshes (quad => 2 triangles)

import bpy

mode = 'TRIANGULATE'
modifier_name = 'triangulator'

objects = bpy.data.objects
meshes = []

for obj in objects:
    if obj.type == "MESH":
        meshes.append(obj)

for obj in meshes:
    # set it as active object
    bpy.context.view_layer.objects.active = obj
    # create modifier
    modifier = obj.modifiers.new(modifier_name, mode)
    modifier.quad_method = 'FIXED'
    modifier.keep_custom_normals = True
    # apply modifier
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier=modifier_name)

