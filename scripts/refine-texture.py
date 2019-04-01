import numpy
from PIL import Image, ImageDraw
import os
import json

UV_MAP = '../models/mountain-gltf/tile1/uv_coord.json'
IMG_QUALITY = 25

abs_uv_map = os.path.abspath(UV_MAP)

with open(abs_uv_map) as file:
    maps = json.load(file)

    img_corresponding = []

    for idx, map in enumerate(maps['maps']):

        if map['image']['mimeType'] != 'image/jpeg' and map['image']['mimeType'] != 'image/png':
            print('only allow texture images in JPEG/PNG format')
            continue

        abs_img_path = os.path.abspath( os.path.join(os.path.dirname(abs_uv_map), map['image']['uri']) )
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
        new_image.save(os.path.abspath( os.path.join(os.path.dirname(abs_img_path), img_basename + '_refined.jpg') ), 'JPEG', quality = IMG_QUALITY)

        img.close()
        new_image.close()
        mask_img.close()

        # save old <--> new texture name mapping
        img_corresponding.append({"old": map['image']['uri'], "new": map['image']['uri'].replace(img_basename + '.' + img_ext, img_basename + '_refined.jpg')})

    abs_output_path = os.path.abspath( os.path.join(os.path.dirname(abs_uv_map), 'refined_texture_map.json') )
    with open(abs_output_path, 'w') as outfile:  
        json.dump(img_corresponding, outfile)
