#include <X11/Xlib.h>
#include <X11/extensions/XShm.h>

struct ImageCapture;

struct ImageCapture* NewImageCapture(int width, int height);

// The return pointer's data will be overwritten the next time this function is
// called
char *CaptureImage(const struct ImageCapture *capture, int x, int y);

void DeleteImageCapture(struct ImageCapture *capture);
