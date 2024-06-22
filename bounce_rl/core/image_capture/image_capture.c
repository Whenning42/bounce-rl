#include "image_capture.h"

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/extensions/XShm.h>
#include <X11/extensions/Xcomposite.h>
#include <assert.h>
#include <stdlib.h>
#include <sys/shm.h>
#include <sys/stat.h>

#include <stdio.h>

struct ImageCapture {
  Display *display;
  int screen;
  XImage *image;
  Pixmap src_pixmap;
  XShmSegmentInfo shminfo;
  void* handler;
  int x;
  int y;
};

capture_t SetupImageCapture(int x, int y, int width, int height, Window window) {
  struct ImageCapture* capture = malloc(sizeof(struct ImageCapture));
  capture->x = x;
  capture->y = y;

  Display *display = XOpenDisplay(NULL);
  int screen = XDefaultScreen(display);

  XImage *image =
      XShmCreateImage(display, DefaultVisual(display, screen), 24, ZPixmap,
                      NULL, &capture->shminfo, width, height);

  XCompositeRedirectWindow(display, window, CompositeRedirectAutomatic);
  Pixmap src_pixmap = XCompositeNameWindowPixmap(display, window);

  // Creates a new shared memory segment large enough for the image with read
  // write permissions
  capture->shminfo.shmid = shmget(IPC_PRIVATE, image->bytes_per_line * image->height,
                         IPC_CREAT | S_IRWXU);
  capture->shminfo.readOnly = False;

  assert(capture->shminfo.shmid != -1);

  image->data = (char *)shmat(capture->shminfo.shmid, NULL, 0);
  capture->shminfo.shmaddr = image->data;

  XShmAttach(display, &capture->shminfo);
  capture->display = display;
  capture->screen = screen;
  capture->image = image;
  capture->src_pixmap = src_pixmap;

  return capture;
}

char *CaptureImage(const capture_t capture_h) {
  const struct ImageCapture* capture = capture_h;
  XShmGetImage(capture->display, capture->src_pixmap, capture->image, capture->x, capture->y, AllPlanes);
  return capture->image->data;
}

void CleanupImageCapture(capture_t capture_h) {
    struct ImageCapture* capture = capture_h;
    assert(XShmDetach(capture->display, &capture->shminfo));
    XDestroyImage(capture->image);
    XFreePixmap(capture->display, capture->src_pixmap);
    shmdt(capture->shminfo.shmaddr);
    shmctl(capture->shminfo.shmid, IPC_RMID, 0);
    XCloseDisplay(capture->display);
    free(capture);
}

int (*global_mim)(Display*, XErrorEvent*, void*) = NULL;
void* global_py_handler = NULL;

int _call_global_handler(Display* display, XErrorEvent* error) {
    return global_mim(display, error, global_py_handler);
}

void SetErrorHandler(OnErrorMIM mim, void* on_error_py) {
  global_mim = mim;
  global_py_handler = on_error_py;
  XSetErrorHandler(_call_global_handler);
}
