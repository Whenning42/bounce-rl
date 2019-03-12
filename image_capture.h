#include <X11/Xlib.h>
#include <X11/extensions/XShm.h>

struct ImageCapture {
  Display *display;
  int screen;
  XImage *image;
  XShmSegmentInfo shminfo;
};

struct ImageCapture InitImageCapture(int width, int height);
char *CaptureImage(const struct ImageCapture *capture, int x, int y);
void CleanupImageCapture(struct ImageCapture *capture);
