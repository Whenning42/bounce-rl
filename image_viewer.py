import image_capture
import numpy as np
from PIL import Image

#import pdb
#pdb.set_trace()

width = 640
height = 480

capture = image_capture.ImageCapture(width, height)
bitmap = capture.get_image(0, 0)
print(bitmap)

img = Image.new( 'RGB', (width, height), "black") # Create a new black image
pixels = img.load() # Create the pixel map

for x in range(img.size[0]):    # For every pixel:
    for y in range(img.size[1]):
#        pixels[x, y] = (100, x, 0)
        pixels[x, y] = (bitmap[y, x, 2], bitmap[y, x, 1], bitmap[y, x, 0])

img.show()
