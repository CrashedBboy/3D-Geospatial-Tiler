import bpy
import bmesh

faces = [1, 2, 3]
cube = bpy.data.objects['Cube']
cube.select_set(True)
bpy.context.view_layer.objects.active = cube

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')

bm = bmesh.from_edit_mesh(cube.data)

for face in bm.faces:
    if face.index in faces:
        face.select_set(True)

bmesh.update_edit_mesh(cube.data, True)

bpy.ops.mesh.separate(type='SELECTED')

bpy.ops.object.mode_set(mode='OBJECT')