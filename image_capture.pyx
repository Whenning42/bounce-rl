cimport image_capture

#import numpy as np
cimport numpy as np

np.import_array()

cdef class ImageCapture:
    cdef image_capture.capture_t _image_capture
    cdef int _width
    cdef int _height

    def __cinit__(self, width, height):
        self._image_capture = image_capture.SetupImageCapture(width, height)
        self._width = width
        self._height = height

    def __dealloc__(self):
        image_capture.CleanupImageCapture(self._image_capture)

    def get_image(self, x = 0, y = 0):
        cdef np.npy_intp shape[3]
        shape[0] = self._height
        shape[1] = self._width
        shape[2] = 4
        cdef char* image_data = image_capture.CaptureImage(self._image_capture, x, y)
        cdef np.ndarray[np.uint8_t, ndim=3] np_array = np.PyArray_SimpleNewFromData(3, shape, np.NPY_UINT8, image_data)
        return np_array
