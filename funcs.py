import os.path as path
import bpy
import bmesh
import math
import numpy
from PIL import Image, ImageDraw
import json

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

    percentage = 1/DECIMATE_LEVEL_RATIO**(total_level - current_level)

    if percentage < MINIMUM:
        percentage = MINIMUM
    
    return percentage

# clear all loaded objects (load empty blender template)
def clear_all():
    bpy.ops.wm.read_homefile(use_empty=True)

# reduce number of meshes in 3d model
def mesh_decimate(target, ratio):
    print("ACTION: decimate mesh to", str(ratio*100)+"%")

    MODE = 'DECIMATE'
    MODIFIER_NAME = 'decimator'

    if target.type != "MESH":
        print("target object is not MESH type")
    else:
        bpy.context.view_layer.objects.active = target
        modifier = target.modifiers.new(MODIFIER_NAME, MODE)
        modifier.decimate_type = 'COLLAPSE'
        modifier.ratio = ratio
        modifier.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier=MODIFIER_NAME)

# get list of mesh objects
def get_mesh_list():

    mesh_list = []

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            mesh_list.append(obj)

    return mesh_list

def get_new_created_mesh(old_mesh_list):
    new_mesh_list = get_mesh_list()
    
    new_created = []

    for m in new_mesh_list:
        if (m not in old_mesh_list):
            new_created.append(m)

    return new_created

def get_mesh_center(target):

    if (target.type != "MESH"):
        print("target object is not MESH type")
        return

    x_min, x_max = math.inf, (-1) * math.inf
    y_min, y_max = math.inf, (-1) * math.inf

    # visit all vertices, get coordinate range in xy-plane and center position(x,y)
    for v in target.data.vertices:
        if v.co.x < x_min:
            x_min = v.co.x
        elif v.co.x > x_max:
            x_max = v.co.x
        if v.co.y < y_min:
            y_min = v.co.y
        elif v.co.y > y_max:
            y_max = v.co.y
    center = [(x_min+x_max)/2, (y_min+y_max)/2]

    return center

def tile_model(root_object, target_level, total_level):
    print("ACTION: tiling level", target_level, "of", total_level)

    if (root_object.type != "MESH"):
        print("target object is not MESH type")
        return

    tile_queue = []

    tile_queue.append( { "level": 0, "x": 0, "y": 0 , "name": root_object.name} )

    while (len(tile_queue) > 0):

        # get first element in queue
        target = tile_queue[0]

        # check whether its level < target level
        if target["level"] == target_level:
            break

        current_level = target["level"]
        gap = 2**(total_level - current_level - 1)

        # get mesh center
        center = get_mesh_center(bpy.data.objects[target["name"]])

        # split it into 4 pieces and rename it
        
        # tile_1_0
        old_meshes = get_mesh_list()
        bpy.context.view_layer.objects.active = bpy.data.objects[target["name"]]

        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(bpy.data.objects[target["name"]].data)

        selected = 0
        bpy.ops.mesh.select_all(action='DESELECT')
        for face in bm.faces:
            should_select = False
            for v in face.verts:
                if v.co.x >= center[0] and v.co.y >= center[1]:
                    should_select = True
                    break
            if (should_select):
                face.select_set(True)
                selected += 1
        bmesh.update_edit_mesh(bpy.data.objects[target["name"]].data, True)

        if (selected > 0):
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.mode_set(mode='OBJECT')
            new_created = get_new_created_mesh(old_meshes)
            if len(new_created) == 1:
                # push sub-meshes into queue
                tile_queue.append( { "level": current_level+1, "x": target["x"]+gap, "y": target["y"], "name": new_created[0].name} )

        # tile_1_1
        old_meshes = get_mesh_list()
        bpy.context.view_layer.objects.active = bpy.data.objects[target["name"]]

        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(bpy.data.objects[target["name"]].data)

        selected = 0
        bpy.ops.mesh.select_all(action='DESELECT')
        for face in bm.faces:
            should_select = False
            for v in face.verts:
                if v.co.x >= center[0]:
                    should_select = True
                    break
            if (should_select):
                face.select_set(True)
                selected += 1
        bmesh.update_edit_mesh(bpy.data.objects[target["name"]].data, True)
        if (selected > 0):
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.mode_set(mode='OBJECT')
            new_created = get_new_created_mesh(old_meshes)
            if len(new_created) == 1:
                # push sub-meshes into queue
                tile_queue.append( { "level": current_level+1, "x": target["x"]+gap, "y": target["y"]+gap, "name": new_created[0].name} )

        # tile_0_0
        old_meshes = get_mesh_list()
        bpy.context.view_layer.objects.active = bpy.data.objects[target["name"]]

        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(bpy.data.objects[target["name"]].data)

        selected = 0
        bpy.ops.mesh.select_all(action='DESELECT')
        for face in bm.faces:
            should_select = False
            for v in face.verts:
                if v.co.y >= center[1]:
                    should_select = True
                    break
            if (should_select):
                face.select_set(True)
                selected += 1
        bmesh.update_edit_mesh(bpy.data.objects[target["name"]].data, True)
        if (selected > 0):
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.mode_set(mode='OBJECT')
            new_created = get_new_created_mesh(old_meshes)
            if len(new_created) == 1:
                # push sub-meshes into queue
                tile_queue.append( { "level": current_level+1, "x": target["x"], "y": target["y"], "name": new_created[0].name} )

        # tile_0_1
        old_meshes = get_mesh_list()
        bpy.context.view_layer.objects.active = bpy.data.objects[target["name"]]

        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(bpy.data.objects[target["name"]].data)

        selected = 0
        bpy.ops.mesh.select_all(action='DESELECT')
        for face in bm.faces:
            face.select_set(True)
            selected += 1
        bmesh.update_edit_mesh(bpy.data.objects[target["name"]].data, True)
        if (selected > 0):
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.mode_set(mode='OBJECT')
            new_created = get_new_created_mesh(old_meshes)
            if len(new_created) == 1:
                # push sub-meshes into queue
                tile_queue.append( { "level": current_level+1, "x": target["x"], "y": target["y"]+gap, "name": new_created[0].name} )

        # pop the first in queue
        tile_queue.pop(0)

    bpy.ops.object.mode_set(mode='OBJECT')
    return tile_queue

def refine_texture(tile):
    print("ACTION: refine texture of model", tile["level"], tile["x"], tile["y"])

    abs_uv_map = path.join(path.dirname(tile['gltf_path']), 'uv_coord.json')

    jpeg_quality = math.ceil(100 / (1.414)**(tile["total_level"] - tile["level"]))

    with open(abs_uv_map) as file:
        maps = json.load(file)

        img_corresponding = []

        for idx, map in enumerate(maps['maps']):

            if map['image']['mimeType'] != 'image/jpeg' and map['image']['mimeType'] != 'image/png':
                print('only allow texture images in JPEG/PNG format')
                continue

            abs_img_path = path.abspath( path.join(path.dirname(abs_uv_map), map['image']['uri']) )
            img_ext = map['image']['uri'].split('.')[-1]
            img_basename = map['image']['uri'].split('/')[-1].split('.' + img_ext)[0]

            # read image as RGB
            img = Image.open(abs_img_path).convert("RGB")
            img_array = numpy.asarray(img)
            img_width, img_height = img_array.shape[1], img_array.shape[0]

            # create new image ("1-bit pixels, black and white", (width, height), "default color")
            mask_img = Image.new('1', (img_width, img_height), 0)

            # set uv polygon area in mask matrix to 1
            for id, face_uv in enumerate(map['faceUvs']):
                polygon = []
                for uv in face_uv:
                    if uv:
                        polygon.append( ( round(uv[0] * img_width), round(uv[1] * img_height) ) )
                if len(polygon) >= 2:
                    ImageDraw.Draw(mask_img).polygon(polygon, outline=1, fill=1)
                    mask = numpy.array(mask_img)
            
            mask = numpy.array(mask_img)

            # assemble new image (uint8: 0-255)
            new_img_array = numpy.empty(img_array.shape, dtype='uint8')

            # copy color values (RGB)
            new_img_array[:,:,:3] = img_array[:,:,:3]

            # filtering image by mask
            new_img_array[:,:,0] = new_img_array[:,:,0] * mask
            new_img_array[:,:,1] = new_img_array[:,:,1] * mask
            new_img_array[:,:,2] = new_img_array[:,:,2] * mask

            # back to Image from numpy
            new_image = Image.fromarray(new_img_array, "RGB")
            new_image.save(path.abspath( path.join(path.dirname(abs_img_path), img_basename + '_refined.jpg') ), 'JPEG', quality = jpeg_quality)

            img.close()
            new_image.close()
            mask_img.close()

            # save old <--> new texture name mapping
            img_corresponding.append({"old": map['image']['uri'], "new": map['image']['uri'].replace(img_basename + '.' + img_ext, img_basename + '_refined.jpg')})

        abs_output_path = path.abspath( path.join(path.dirname(abs_uv_map), 'refined_texture_map.json') )
        with open(abs_output_path, 'w') as outfile:  
            json.dump(img_corresponding, outfile)
