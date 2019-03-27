#include <X11/Xlib.h>
#include <X11/extensions/XShm.h>

typedef void* capture_t;

// Allocates and initializes an ImageCapture
capture_t SetupImageCapture(int width, int height);

// The return pointer's data will be overwritten the next time this function is
// called
char *CaptureImage(const capture_t capture, Window window);

// Cleans up and delete the given ImageCapture
void CleanupImageCapture(capture_t capture);
