from PIL import Image
im1 = Image.open('model/house_m100/house_diffuse.jpg')

# here, we create an empty string buffer    
im1.save('model/house_m100/house_diffuse.jpg', "JPEG", quality=50)