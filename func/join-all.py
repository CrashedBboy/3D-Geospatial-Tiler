# join all object into one
import bpy

active_set = False

bpy.ops.object.select_all(action='DESELECT')

# looking for mesh objects
print("finding mesh objects...")
for i, obj in enumerate(bpy.data.objects):
    if obj.type == "MESH":
        print("found:", obj.name)
        # set first mesh object as active object
        if not active_set:
            active_set = True
            bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

print(str(len(bpy.context.selected_objects)), "mesh object(s) found, join them together")

# if more than one mesh object found, join them together
if active_set and len(bpy.context.selected_objects) >= 2:
    bpy.ops.object.join()
