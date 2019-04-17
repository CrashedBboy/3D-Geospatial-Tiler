# export model's texture images to files

import bpy
import os.path as path

import PIL.Image as Image
import numpy as np

import time
import math

OUTPUT_DIR = "C:\\Users\\CrashedBboy\\\Desktop\\tmp"

absolute_output_dir = path.abspath(OUTPUT_DIR)

if (not path.exists(absolute_output_dir)):
    print("output dir not exists")
    exit()

# memory consumption
# width * height * channels * (8+4)  bytes
# (8+4): values in blender array use float64, values in our np array use float32

count = 0
for img in bpy.data.images:
    if (img.type == "IMAGE"):
        print("find", img.name)
        target_channels = channels = img.channels
        if target_channels >= 3:
            target_channels = 3

        start = time.time()
        print("copy pixels")
        copied_pixels = img.pixels[:]
        print("exec time:", math.ceil(time.time()-start), "s")

        start = time.time()
        print("create numpy array")
        pixels = np.array(copied_pixels)
        print("exec time:", math.ceil(time.time()-start), "s")

        start = time.time()
        print("clear copied pixels")
        copied_pixels = None
        print("exec time:", math.ceil(time.time()-start), "s")

        start = time.time()
        print("multiply 255")
        pixels = pixels * 255
        print("exec time:", math.ceil(time.time()-start), "s")

        start = time.time()
        print("convert to uint8")
        pixels = pixels.astype(np.uint8)
        print("exec time:", math.ceil(time.time()-start), "s")

        start = time.time()
        print("reshape")
        pixels = pixels.reshape((img.size[1], img.size[0], channels))
        print("exec time:", math.ceil(time.time()-start), "s")

        start = time.time()
        print("take out channels")
        pixels = pixels[:,:, 0:target_channels]
        print("exec time:", math.ceil(time.time()-start), "s")

        start = time.time()
        print("flip")
        pixels = np.flip(pixels, 0)
        print("exec time:", math.ceil(time.time()-start), "s")

        filename = "Image_" + str(count) + ".jpg"
        count += 1

        start = time.time()
        print("save")
        Image.fromarray(pixels).save(path.join(absolute_output_dir, filename), 'JPEG')
        print("exec time:", math.ceil(time.time()-start), "s")

        pixels = None