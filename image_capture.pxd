cdef extern from "src/image_capture.h":
    ctypedef void* capture_t

    capture_t SetupImageCapture(int width, int height)
    char *CaptureImage(capture_t capture_h, long long window)
    void CleanupImageCapture(capture_t capture_h)

