import os.path as path
import bpy
import math

# delete every object (including camera and light source) in the scene
def clear_default():
    print("ACTION: clear all default objects(cube, lamp, camera) in the scene.")
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=True)

# import GLTF model
def import_gltf(filepath = None):
    print("ACTION: import GLTF model")

    if (filepath == None) or (not path.isfile(filepath)):
        print("invalid filepath")
        return False

    else:
        # data type "set" returned
        return bpy.ops.import_scene.gltf(
            filepath = filepath,
            import_pack_images = True,
            import_shading = 'NORMALS'
            )

# import OBJ model
def import_obj(filepath = None):
    print("ACTION: import OBJ model")

    if (filepath == None) or (not path.isfile(filepath)):
        print("invalid filepath")
        return False
    else:
        # data type "set" returned
        return bpy.ops.import_scene.obj(
            filepath = filepath,
            use_edges = True,
            use_smooth_groups = True,
            use_split_objects = True,
            use_split_groups = False,
            use_groups_as_vgroups = False,
            use_image_search = True,
            split_mode = 'ON',
            global_clight_size = 0.0,
            axis_forward = '-Z',
            axis_up = 'Y'
            )

# join all object into one
def join_all():
    print("ACTION: join all object into one")

    active_set = False

    bpy.ops.object.select_all(action='DESELECT')

    # looking for mesh objects
    print("finding mesh objects...")
    for i, obj in enumerate(bpy.data.objects):
        if obj.type == "MESH":
            # set first mesh object as active object
            if not active_set:
                active_set = True
                bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

    print(str(len(bpy.context.selected_objects)), "mesh object(s) found, join them together")

    # if more than one mesh object found, join them together
    if active_set and len(bpy.context.selected_objects) >= 2:
        bpy.ops.object.join()

# triangulate meshes (e.g. 1 square -> 2 triangles)
def triangulate():
    print("ACTION: triangulate meshes")

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

# export model in gltf format
# note: Blender under version 2.8 does not support exporting gltf by default
def export_gltf(filepath=None, format='GLTF_SEPARATE', copyright='', camera=False, selected=False, animation=False, light=False):
    print("ACTION: export to GLTF")

    if (filepath == None) or (not path.isdir(path.dirname(filepath))):
        print("Invalid output path")
        return False
    else:
        return bpy.ops.export_scene.gltf(
            export_format = format, # 'GLB', 'GLTF_EMBEDDED', 'GLTF_SEPARATE'
            export_copyright = copyright,
            export_texcoords = True,
            export_normals = True,
            export_materials = True,
            export_colors = True,
            export_cameras = camera,
            export_selected = selected,
            export_extras = False,
            export_yup = True,
            export_apply = False,
            export_animations = animation,
            export_frame_range = animation,
            export_lights = light,
            filepath = filepath
            )

# get model's information
# including vertices/faces/uv-mapping count and file size of texture images.
def get_proper_level(filepath = None):
    print("ACTION: compute model tiling level")

    LEVEL_MAX = 5

    if (filepath == None) or (path.exists(filepath) == False):
        print("file", filepath, "not found")
        return None
    else:
        file_size = path.getsize(filepath) / (1024*1024) # in MBs
        level = math.ceil(math.log(file_size, 4))

        if level < 0:
            level = 0
        
        if level > LEVEL_MAX:
            level = LEVEL_MAX

        print("proper tiling level:", level)
        return level

# get decimate ratio for models of each level
def get_decimate_percentage(current_level, total_level):

    DECIMATE_LEVEL_RATIO = 1.414 # square root of 2
    MINIMUM = 0.2

    percentage = 100/DECIMATE_LEVEL_RATIO**(total_level - current_level)

    if percentage < MINIMUM:
        percentage = MINIMUM
    
    return percentage