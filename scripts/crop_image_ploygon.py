import numpy
from PIL import Image, ImageDraw

# read image as RGB
img = Image.open("crop.jpg").convert("RGB")

# convert to numpy (for convenience)
img_array = numpy.asarray(img)

# create mask
polygon = [(444,203),(623,243),(691,177),(581,26),(482,42)]

# create new image ("1-bit pixels, black and white", (width, height), "default color")
mask_img = Image.new('1', (img_array.shape[1], img_array.shape[0]), 0)

ImageDraw.Draw(mask_img).polygon(polygon, outline=1, fill=1)
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
new_img = Image.fromarray(new_img_array, "RGB")
new_img.save("out.jpg")