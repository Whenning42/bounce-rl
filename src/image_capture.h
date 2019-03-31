#include <X11/Xlib.h>
#include <X11/extensions/XShm.h>

typedef void* capture_t;
typedef int (*OnErrorMIM)(Display*, XErrorEvent*, void*);

// Allocates and initializes an ImageCapture
capture_t SetupImageCapture(int width, int height);

// The return pointer's data will be overwritten the next time this function is
// called
char *CaptureImage(const capture_t capture, Window window);

// Cleans up and delete the given ImageCapture
void CleanupImageCapture(capture_t capture);

// Sets the X error handler for this library's calls to a python function
void SetErrorHandler(OnErrorMIM mim, void* on_error_py);
