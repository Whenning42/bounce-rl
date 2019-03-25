cdef extern from "src/image_capture.h":
    ctypedef void* capture_t

    capture_t SetupImageCapture(int width, int height)
    char *CaptureImage(capture_t capture_h, int x, int y)
    void CleanupImageCapture(capture_t capture_h)

