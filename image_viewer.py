import image_capture
from harness import *
import numpy as np
from Xlib import display
from PIL import Image
import time

# Image capture test

width = 640
height = 480

root_window = display.Display().screen().root.id

capture = image_capture.ImageCapture(width, height)
bitmap = capture.get_image(root_window)

img = Image.new( 'RGB', (width, height), "black") # Create a new black image
pixels = img.load() # Create the pixel map

for x in range(img.size[0]):    # For every pixel:
    for y in range(img.size[1]):
        pixels[x, y] = (bitmap[y, x, 2], bitmap[y, x, 1], bitmap[y, x, 0])

# img.show()

# Harness capture test

harness = Harness()
for i in range(5):
    bitmap = harness.get_screen()
    for x in range(img.size[0]):    # For every pixel:
        for y in range(img.size[1]):
            pixels[x, y] = (bitmap[y, x, 2], bitmap[y, x, 1], bitmap[y, x, 0])
#    img.show()
    time.sleep(5)
