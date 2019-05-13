import os.path as path
import bpy
import bmesh
import math
import numpy as np
from PIL import Image, ImageDraw
import cv2
import json
import subprocess
import shutil

# get program setting constants
def get_settings(program_dir=path.dirname(__file__)):

    if not program_dir:
        return False
    
    settings_filepath = path.abspath(path.join(program_dir, "settings.json"))

    with open(settings_filepath, 'r') as reader:
        settings = json.load(reader)

        return settings

settings = get_settings()

# delete every object (including camera and light source) in the scene
def clear_default():
    print("ACTION: clear all default objects(cube, lamp, camera) in the scene.")
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=True)

# import GLTF model
def import_gltf(filepath = None):
    print("ACTION: import GLTF model:", filepath)

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
def import_obj(filepath = None, axis_forward=settings["AXIS_FORWARD"], axis_up=settings["AXIS_UP"]):
    print("ACTION: import OBJ model:", filepath)

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
            axis_forward = axis_forward,
            axis_up = axis_up
            )

# import COLLADA model
def import_collada(filepath=None):
    print("ACTION: import COLLADA model:", filepath)

    if (filepath == None) or (not path.isfile(filepath)):
        print("invalid filepath")
        return False
    else:
        return bpy.ops.wm.collada_import(filepath=filepath)

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

# limit max size of texture image
def limit_texture(max_size):
    print("ACTION: limit texture image size")

    for img in bpy.data.images:
        if (img.type == "IMAGE"):

            width = img.size[0]
            height = img.size[1]

            resize = False

            if width > max_size:
                resize = True
                width = max_size

            if height > max_size:
                resize = True
                height = max_size

            if (resize):
                img.scale(width, height)

# export texture images to file
def export_texture(image=None, filepath=None):
    print("ACTION: export texture", image.name, "to", filepath)

    target_channels = channels = image.channels
    if target_channels >= 3:
        target_channels = 3

    copied_pixels = image.pixels[:]
    pixels = np.array(copied_pixels)
    copied_pixels = None

    # convert value range from [0,1] to [0,255]
    pixels = pixels * 255
    pixels = pixels.astype(np.uint8)

    # convert to 3d array (width,height,channels)
    pixels = pixels.reshape((image.size[1], image.size[0], channels))

    pixels = pixels[:,:, 0:target_channels]
    pixels = np.flip(pixels, 0)

    cv2.imwrite(filepath, cv2.cvtColor(pixels, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])

    pixels = None

# minimize all texture (to save time while export tiles to glTF models)
def minimize_texture():
    print("ACTION: minimize all texture")

    for img in bpy.data.images:
        if (img.type == "IMAGE"):
            img.scale(1, 1)

# export model in gltf format
# note: Blender under version 2.8 does not support exporting gltf by default
def export_gltf(filepath=None, format='GLTF_SEPARATE', yup=False, selected=False):
    print("ACTION: export to GLTF:", filepath)

    if (filepath == None) or (not path.isdir(path.dirname(filepath))):
        print("Invalid output path")
        return False
    else:
        return bpy.ops.export_scene.gltf(
            export_image_format = "JPEG",
            export_format = format, # 'GLB', 'GLTF_EMBEDDED', 'GLTF_SEPARATE'
            export_copyright = '',
            export_texcoords = True,
            export_normals = True,
            export_materials = True,
            export_colors = True,
            export_cameras = False,
            export_selected = selected,
            export_extras = False,
            export_yup = yup,
            export_apply = False,
            export_animations = False,
            export_frame_range = False,
            export_lights = False,
            filepath = filepath
            )

def export_obj(filepath=None, selected=False, axis_forward=settings["AXIS_FORWARD"], axis_up=settings["AXIS_UP"]):
    print("ACTION: export to OBJ:", filepath)

    if (filepath == None) or (not path.isdir(path.dirname(filepath))):
        print("Invalid output path")
        return False
    else:
        return bpy.ops.export_scene.obj(
            filepath=filepath,
            check_existing=False,
            use_selection=selected,
            use_animation=False,
            use_mesh_modifiers=True,
            use_edges=True,
            use_smooth_groups=False,
            use_smooth_groups_bitflags=False,
            use_normals=True,
            use_uvs=True,
            use_materials=True,
            use_triangles=False,
            use_nurbs=False,
            use_vertex_groups=False,
            use_blen_objects=True,
            group_by_object=False,
            group_by_material=False,
            keep_vertex_order=False,
            global_scale=1.0,
            path_mode='COPY',
            axis_forward=axis_forward,
            axis_up=axis_up
            )

def export_collada(filepath=None, selected=False):
    print("ACTION: export to COLLADA:", filepath)

    if (filepath == None) or (not path.isdir(path.dirname(filepath))):
        print("Invalid output path")
        return False
    else:
        return bpy.ops.wm.collada_export(
            filepath=filepath,
            check_existing=False,
            selected=selected,
            include_children=False,
            include_animations=False,
            include_all_actions=False,
            use_texture_copies=True,
            triangulate=False,
            )

# get model's information
# including vertices/faces/uv-mapping count and file size of texture images.
def get_proper_level(filepath = None):
    print("ACTION: compute model tiling level")

    if (filepath == None) or (path.exists(filepath) == False):
        print("file", filepath, "not found")
        return None
    else:
        file_size = path.getsize(filepath) / (1024*1024) # in MBs
        level = math.ceil(math.log(file_size, 4))

        if level < 0:
            level = 0
        
        if level > settings["LEVEL_MAX"]:
            level = settings["LEVEL_MAX"]

        print("proper tiling level:", level)
        return level

# get decimate ratio for models of each level
def get_decimate_percentage(current_level, total_level):

    percentage = 1/settings["DECIMATE_LEVEL_RATIO"]**(total_level - current_level)

    if percentage < settings["DECIMATE_MIN"]:
        percentage = settings["DECIMATE_MIN"]
    
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

# compare old mesh list with the current to find the new created meshes
def get_new_created_mesh(old_mesh_list):
    new_mesh_list = get_mesh_list()
    
    new_created = []

    for m in new_mesh_list:
        if (m not in old_mesh_list):
            new_created.append(m)

    return new_created

# get grometry center of mesh object
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

# split mesh object into 4
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

# parsing glTF UV coordinates data
def parse_uv(lod_data_path=None):
    print("ACTION: parse glTF UV coordinates data accroding to file list:", lod_data_path)

    if not path.exists(lod_data_path):
        return False
    else:
        node_exec = settings["NODE_EXEC"]
        parser_path = settings["UV_PARSER"]
        uv_parser_proc = subprocess.run([node_exec, parser_path, "--input", lod_data_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return uv_parser_proc

# remove unmapped part of texture images and compress them
def refine_texture(tile, original_textures=None):
    print("ACTION: refine texture of model", tile["level"], tile["x"], tile["y"])

    gltf_dir = path.dirname(tile['gltf_path'])

    if original_textures != None:
        for tex in original_textures:
            print("restore texture", tex, "to", gltf_dir)
            shutil.copy2(tex, gltf_dir)

    abs_uv_map = path.join(gltf_dir, 'uv_coord.json')

    jpeg_quality = math.ceil(85 / (1.414)**(tile["total_level"] - tile["level"]))

    if not path.exists(abs_uv_map):
        return

    with open(abs_uv_map) as file:
        maps = json.load(file)

        img_corresponding = []

        images = []

        for idx, map in enumerate(maps['maps']):

            if map['image']['mimeType'] != 'image/jpeg' and map['image']['mimeType'] != 'image/png':
                print('only allow texture images in JPEG/PNG format')
                continue

            abs_img_path = path.abspath( path.join(path.dirname(abs_uv_map), map['image']['uri']) )
            img_ext = map['image']['uri'].split('.')[-1]
            img_basename = map['image']['uri'].split('/')[-1].split('.' + img_ext)[0]

            # read image as RGB
            img_array = cv2.cvtColor(cv2.imread(abs_img_path), cv2.COLOR_BGR2RGB)
            img_width, img_height = img_array.shape[1], img_array.shape[0]

            # create new image ("1-bit pixels, black and white", (width, height), "default color")
            mask_img = Image.new('1', (img_width, img_height), 0)

            # set uv polygon area in mask matrix to 1
            for id, face_uv in enumerate(map['faceUvs']):
                polygons = []
                for uv in face_uv:
                    if uv:
                        polygons.append( ( round(uv[0] * img_width), round(uv[1] * img_height) ) )
                if len(polygons) >= 2:
                    ImageDraw.Draw(mask_img).polygon(polygons, outline=1, fill=1)
            
            mask = np.array(mask_img, dtype=np.bool)

            mask_img.close()

            # search for image name in array
            found = False
            for img in images:
                if (img["basename"] == img_basename):
                    img["mask"] = np.logical_or(img["mask"], mask)
                    found = True
                    break
            
            if not found:
                images.append({"abs_path": abs_img_path, "rel_path": map['image']['uri'], "ext": img_ext, "basename": img_basename, "mask": mask})

        for i in images:

            # expand the filter a little bit
            expanded_mask = np.zeros(i["mask"].shape, dtype=np.bool)
            for r in range(i["mask"].shape[0]):
                for c in range(i["mask"].shape[1]):

                    if i["mask"][r,c] == 1:
                        for x in range(r-settings["TEX_REFINE_BORDER"], r+settings["TEX_REFINE_BORDER"]+1):
                            for y in range(c-settings["TEX_REFINE_BORDER"], c+settings["TEX_REFINE_BORDER"]+1):
                                if x >= 0 and y >= 0 and (x < expanded_mask.shape[0]) and (y < expanded_mask.shape[1]):
                                    expanded_mask[x,y] = 1

            # read image as RGB
            img_array = cv2.cvtColor(cv2.imread(i["abs_path"]), cv2.COLOR_BGR2RGB)

            # assemble new image (uint8: 0-255)
            new_img_array = np.empty(img_array.shape, dtype='uint8')

            # copy color values (RGB)
            new_img_array[:,:,:3] = img_array[:,:,:3]

            # filtering image by mask
            new_img_array[:,:,0] = new_img_array[:,:,0] * expanded_mask
            new_img_array[:,:,1] = new_img_array[:,:,1] * expanded_mask
            new_img_array[:,:,2] = new_img_array[:,:,2] * expanded_mask

            # back to Image from numpy
            cv2.imwrite(
                path.abspath( path.join(path.dirname(i["abs_path"]), i["basename"] + '_refined.jpg') ),
                cv2.cvtColor(new_img_array, cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
                )

            # save old <--> new texture name mapping
            img_corresponding.append({"old": i["rel_path"], "new": i["rel_path"].replace(i["basename"] + '.' + i["ext"], i["basename"] + '_refined.jpg')})
        
        abs_output_path = path.abspath( path.join(gltf_dir, 'refined_texture_map.json') )
        with open(abs_output_path, 'w') as outfile:  
            json.dump(img_corresponding, outfile)

# update texture image filename in GLTF model
def update_texture(tile):
    print("ACTION: update texture filename of model", tile["level"], tile["x"], tile["y"])

    gltf_dir = path.dirname(tile["gltf_path"])

    if (not path.exists(path.join(gltf_dir, "refined_texture_map.json"))):
        return True
    
    node_exec = settings["NODE_EXEC"]
    updater_path = settings["TEX_UPDATER"]
    texture_updater_proc = subprocess.run([node_exec, updater_path, "--input", tile["gltf_path"]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return texture_updater_proc

# convert all GLTF model to b3dm and generate 3D tileset
def generate_tree_3d_tiles(input_path, output_path, latitude=25.078503, longitude=121.238418, height=0):
    print("ACTION: convert all GLTF model to b3dm and generate 3D tileset")

    if (not path.exists(input_path)) or (not path.exists(output_path)):
        print("input file or output directory is not exist")
        return False
    
    node_exec = settings["NODE_EXEC"]
    generator_path = settings["3DTILES_TREE_GENERATOR"]
    generator_proc = subprocess.run(
        [node_exec, generator_path, "--input", input_path, "--output", output_path, "--latitude", latitude, "--longitude", longitude, "--height", height],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
        )

    return generator_proc

# reset rotation
def reset_rotation(target):
    target.rotation_quaternion[0] = 1
    target.rotation_quaternion[1] = 0
    target.rotation_quaternion[2] = 0
    target.rotation_quaternion[3] = 0
    target.rotation_axis_angle[0] = 0
    target.rotation_euler[0] = 0
    target.rotation_euler[1] = 0
    target.rotation_euler[2] = 0

# convert all GLTF model to b3dm and generate 3D tileset
def generate_flat_3d_tiles(input_path, output_path, latitude=25.078503, longitude=121.238418, height=0):
    print("ACTION: convert all GLTF model to b3dm and generate 3D tileset")

    if (not path.exists(input_path)) or (not path.exists(output_path)):
        print("input file or output directory is not exist")
        return False
    
    node_exec = settings["NODE_EXEC"]
    generator_path = settings["3DTILES_FLAT_GENERATOR"]
    generator_proc = subprocess.run(
        [node_exec, generator_path, "--input", input_path, "--output", output_path, "--latitude", latitude, "--longitude", longitude, "--height", height],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
        )

    return generator_proc