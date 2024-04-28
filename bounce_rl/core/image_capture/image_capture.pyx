cimport image_capture

cimport numpy as np
import Xlib
from Xlib import display

np.import_array()

cdef class ImageCapture:
    cdef image_capture.capture_t _image_capture
    cdef int _width
    cdef int _height

    def __cinit__(self, x, y, width, height):
        self._image_capture = image_capture.SetupImageCapture(x, y, width, height)
        self._width = width
        self._height = height

    def __dealloc__(self):
        image_capture.CleanupImageCapture(self._image_capture)

    def get_image(self, window):
        cdef np.npy_intp shape[3]
        shape[0] = self._height
        shape[1] = self._width
        shape[2] = 4
        cdef char* image_data = image_capture.CaptureImage(self._image_capture, window)
        cdef np.ndarray[np.uint8_t, ndim=3] np_array = np.PyArray_SimpleNewFromData(3, shape, np.NPY_UINT8, image_data)
        return np_array

    @staticmethod
    def set_error_handler(on_error_py):
        image_capture.SetErrorHandler(error_caller, <void*>on_error_py)

cdef int error_caller(Display* display, XErrorEvent* error, void* on_error_py) noexcept:
    (<object>on_error_py)()
    return 0
