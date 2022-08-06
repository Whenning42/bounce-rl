// This approach seems like a dead end. It uses an XGrab to get keyboard events
// and forwards them with XTestFakeKeyEvent. It doesn't seem to work due to the
// grab either affecting event delivery to the client window, or affecting the
// client window's response to the events.

#include <time.h>
#include <iostream>
#include <X11/Xlib.h>
#include <X11/Intrinsic.h>
#include <X11/extensions/XTest.h>

int main(int argc, char *argv[]) {
  Display *display = XOpenDisplay(NULL);
  XEvent ev;
  XGrabKeyboard(display, DefaultRootWindow(display), false, GrabModeAsync,
                GrabModeAsync, CurrentTime);

  Window w = 0x1200014;

  while (true) {
    XNextEvent(display, &ev);

    // Pressing 'Q' exits the program.
    if (ev.xkey.keycode == 24) {
      break;
    }

    // XTestGrabControl(display, true);
    if (ev.type == KeyPress) {
//      if (time(NULL) / 5 % 2 == 0) {
        std::cout << "Sending press" << std::endl;
//        std::cout << "Time: " << time(NULL) << std::endl;
        // XUngrabKeyboard(display, CurrentTime);
        XSetInputFocus(display, w, RevertToNone, CurrentTime);
        XSync(display, false);
        // XSendEvent(display, w, false, KeyPressMask, &ev);
        // XGrabKeyboard(display, DefaultRootWindow(display), false, GrabModeAsync,
        //               GrabModeAsync, CurrentTime);
//      } else {
//        std::cout << "Skipped event." << std::endl;
//      }
      // XSendEvent(display, PointerWindow, false, KeyPressMask, &ev);
      XTestFakeKeyEvent(display, (uint32_t)XKeysymToKeycode(display, XK_Return), true, CurrentTime);
    } else if (ev.type == KeyRelease) {
      // std::cout << "Sending release" << std::endl;
      // XUngrabKeyboard(display, CurrentTime);
      // XSetInputFocus(display, w, RevertToNone, CurrentTime);
      // XSendEvent(display, w, false, KeyReleaseMask, &ev);
      // XGrabKeyboard(display, DefaultRootWindow(display), false, GrabModeAsync,
      //               GrabModeAsync, CurrentTime);
      // XSendEvent(display, PointerWindow, false, KeyReleaseMask, &ev);
      XTestFakeKeyEvent(display, (uint32_t)XKeysymToKeycode(display, XK_Return), false, CurrentTime);
    }
    XSync(display, false);
    // XTestGrabControl(display, false);
  }
}
