#include "image_capture.h"

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/extensions/XShm.h>
#include <assert.h>
#include <stdlib.h>
#include <sys/shm.h>
#include <sys/stat.h>

#include <stdio.h>

struct ImageCapture {
  Display *display;
  int screen;
  XImage *image;
  XShmSegmentInfo shminfo;
};

capture_t SetupImageCapture(int width, int height) {
  struct ImageCapture* capture = malloc(sizeof(struct ImageCapture));

  Display *display = XOpenDisplay(NULL);
  int screen = XDefaultScreen(display);

  XImage *image =
      XShmCreateImage(display, DefaultVisual(display, screen), 24, ZPixmap,
                      NULL, &capture->shminfo, width, height);

  // Creates a new shared memory segment large enough for the image with read
  // write permissions
  capture->shminfo.shmid = shmget(IPC_PRIVATE, image->bytes_per_line * image->height,
                         IPC_CREAT | S_IRWXU);
  capture->shminfo.readOnly = False;

  printf("Shmid is: %d\n", capture->shminfo.shmid);
  assert(capture->shminfo.shmid != -1);

  image->data = (char *)shmat(capture->shminfo.shmid, NULL, 0);
  capture->shminfo.shmaddr = image->data;

  XShmAttach(display, &capture->shminfo);
  capture->display = display;
  capture->screen = screen;
  capture->image = image;
  return capture;
}

  #include <time.h>
char *CaptureImage(const capture_t capture_h, int x, int y) {
  const struct ImageCapture* capture = capture_h;

  clock_t start = clock();
  XShmGetImage(capture->display, RootWindow(capture->display, capture->screen), capture->image, x, y, AllPlanes);
  printf("Took: %fs\n", ((double) (clock() - start)) / CLOCKS_PER_SEC);

  return capture->image->data;
}

void CleanupImageCapture(capture_t capture_h) {
    struct ImageCapture* capture = capture_h;
    assert(XShmDetach(capture->display, &capture->shminfo));
    XDestroyImage(capture->image);
    shmdt(capture->shminfo.shmaddr);
    shmctl(capture->shminfo.shmid, IPC_RMID, 0);
    free(capture);
}
