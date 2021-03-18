cimport camera_node
cimport numpy as np
import numpy as np_py

cdef class CameraNode:
    cdef camera_node.camera_node_t _camera_node
    cdef int _width
    cdef int _height

    def __cinit__(self, width, height):
        self._camera_node = camera_node.CreateCameraNode(width, height)
        self._width = width
        self._height = height

    def __dealloc__(self):
        camera_node.DeleteCameraNode(self._camera_node)

    def Publish(self, bitmap):
        if not bitmap.flags['C_CONTIGUOUS']:
            bitmap = np_py.ascontiguousarray(bitmap)
        cdef char[:, :, ::1] bitmap_view = bitmap
        camera_node.PublishImage(self._camera_node, &bitmap_view[0, 0, 0])
