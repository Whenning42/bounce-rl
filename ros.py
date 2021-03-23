import camera_node
import numpy as np

class ROSCameraNode:
    def __init__(self, width, height):
        self.node = camera_node.CameraNode(width, height)

    def update(self, bitmap):
        self.node.Publish(bitmap)
        return np.zeros(84)
