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
char *CaptureImage(const capture_t capture_h, Window window) {
  const struct ImageCapture* capture = capture_h;

  clock_t start = clock();
  XShmGetImage(capture->display, window, capture->image, 0, 0, AllPlanes);
  double duration = ((double)(clock() - start)) / CLOCKS_PER_SEC;

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

void FocusAndIgnoreAllEvents(capture_t capture_h, Window window) {
    struct ImageCapture* capture = capture_h;
    Display* display = capture->display;

    int num_details = 8;
    int details[] = {NotifyAncestor, NotifyVirtual, NotifyInferior, NotifyNonlinear, NotifyNonlinearVirtual, NotifyPointer, NotifyPointerRoot, NotifyDetailNone};

    // Sends the focus in event
    for(int i = 0; i < num_details; ++i) {
        XEvent focus_in;
        focus_in.type = FocusIn;
        focus_in.xfocus.display = display;
        focus_in.xfocus.window = window;
        focus_in.xfocus.mode = NotifyNormal;
        focus_in.xfocus.detail = details[i];
        assert(XSendEvent(display, window, /*propagate=*/False, 0/*?*/, &focus_in));
        XSelectInput(display, window, FocusChangeMask);
    }

    XFlush(display);
    printf("Did it!\n");
}
