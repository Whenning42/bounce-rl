cdef extern from "src/image_capture.h":
    ctypedef void* capture_t
    ctypedef struct XErrorEvent:
        int type;
        void *display;  # Display the event was read from
        unsigned long serial;  # serial number of failed request
        unsigned char error_code; # error code of failed request
        unsigned char request_code; # Major op-code of failed request
        unsigned char minor_code; # Minor op-code of failed request
        unsigned long resourceid;   # resource id
    ctypedef long long Display;
    ctypedef int (*OnErrorMIM)(Display*, XErrorEvent*, void*)

    capture_t SetupImageCapture(int width, int height)
    char *CaptureImage(capture_t capture_h, long long window)
    void CleanupImageCapture(capture_t capture_h)
    void SetErrorHandler(OnErrorMIM mim, void* on_error_py)
