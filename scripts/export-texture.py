# export model's texture images to files

import bpy
import os.path as path

import PIL.Image as Image
import numpy as np

OUTPUT_DIR = "C:\\Users\\CrashedBboy\\\Desktop\\tmp"

absolute_output_dir = path.abspath(OUTPUT_DIR)

if (not path.exists(absolute_output_dir)):
    print("output dir not exists")
    exit()

count = 0
for img in bpy.data.images:
    if (img.type == "IMAGE"):
        print("find", img.name)
        target_channels = channels = img.channels
        if target_channels >= 3:
            target_channels = 3

        print("copy pixels")
        copied_pixels = img.pixels[:]

        print("create numpy array")
        pixels = np.array(copied_pixels)

        print("multiply 255")
        pixels = pixels * 255

        print("convert to uint8")
        pixels = pixels.astype(np.uint8)

        print("reshape")
        pixels = pixels.reshape((img.size[1], img.size[0], channels))

        print("take out channels")
        pixels = pixels[:,:, 0:target_channels]

        print("flip")
        pixels = np.flip(pixels, 0)

        filename = "Image_" + str(count) + ".jpg"
        count += 1

        print("save")
        Image.fromarray(pixels).save(path.join(absolute_output_dir, filename), 'JPEG')

        pixels = None