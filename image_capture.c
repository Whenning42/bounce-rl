#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/extensions/XShm.h>
#include <assert.h>
#include <sys/shm.h>

struct ImageCapture {
  Display *display;
  int screen;
  XImage *image;
  XShmSegmentInfo shminfo;
};

struct ImageCapture InitImageCapture(int width, int height) {
  Display *display = XOpenDisplay(NULL);
  int screen = XDefaultScreen(display);
  Visual* visual = DefaultVisual(display, screen);
  XShmSegmentInfo shminfo;

  XImage *image =
      XShmCreateImage(display, DefaultVisual(display, screen), 24, ZPixmap,
                      NULL, &shminfo, width, height);

  // Creates a new shared memory segment large enough for the image with read
  // write permissions
  shminfo.shmid = shmget(IPC_PRIVATE, image->bytes_per_line * image->height,
                         IPC_CREAT | 0x777);

  image->data = (char *)shmat(shminfo.shmid, NULL, 0);
  shminfo.shmaddr = image->data;

  assert(XShmAttach(display, &shminfo));
  struct ImageCapture capture = {
      .display = display, .screen = screen, .image = image, .shminfo = shminfo};
  return capture;
}

char *CaptureImage(const struct ImageCapture *capture, int x, int y) {
  XShmGetImage(capture->display, RootWindow(capture->display, capture->screen), capture->image, x, y, AllPlanes);
  return capture->image->data;
}

void CleanupImageCapture(struct ImageCapture *capture) {
    assert(XShmDetach(capture->display, &capture->shminfo));
    XDestroyImage(capture->image);
    shmdt(capture->shminfo.shmaddr);
    shmctl(capture->shminfo.shmid, IPC_RMID, 0);
}
