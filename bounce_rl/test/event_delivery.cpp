// A test set up to explore how a window responds to core and xi2 events,
// with and without sendevent bits overridden.

#include <iostream>
#include <string>
#include <unistd.h>
#include <cstring>

#include <X11/Xlib.h>
#include <X11/extensions/XInput2.h>
#include <X11/keysym.h>


int main(int argc, char **argv)
{
    if (argc != 3)
    {
        std::cerr << "Usage: " << argv[0] << " <window_id> <test_id>" << std::endl;
        return 1;
    }

    Display *display = XOpenDisplay(NULL);
    Window target_window = std::stoi(argv[1], nullptr, 16);
    std::cout << "Target window: " << target_window << std::endl;
    Window root = DefaultRootWindow(display);

    int test_id = std::stoi(argv[2]);

    // Core + Send event bit
    if (test_id == 0) // Appears to be WAI!?
    {
        std::cout << "Running core event test." << std::endl;
        sleep(1);
        XEvent event;

        // Set input focus.
        XSetInputFocus(display, target_window, RevertToParent, CurrentTime);
        XFlush(display);


        // Send enter notify.
        memset(&event, 0, sizeof(event));
        event.type = EnterNotify;
        event.xcrossing.window = target_window;
        event.xcrossing.root = root;
        event.xcrossing.subwindow = None;
        event.xcrossing.time = CurrentTime;
        event.xcrossing.x = 100;
        event.xcrossing.y = 100;
        event.xcrossing.x_root = 100;
        event.xcrossing.y_root = 100;
        event.xcrossing.mode = NotifyNormal;
        event.xcrossing.detail = NotifyNonlinear;
        event.xcrossing.same_screen = True;
        event.xcrossing.focus = True;
        event.xcrossing.state = 0;
        XSendEvent(display, target_window, True, EnterWindowMask, &event);
        XFlush(display);

        // Send focus in.
        memset(&event, 0, sizeof(event));
        event.type = FocusIn;
        event.xfocus.window = target_window;
        event.xfocus.mode = NotifyNormal;
        event.xfocus.detail = NotifyNonlinear;
        XSendEvent(display, target_window, True, FocusChangeMask, &event);
        XFlush(display);

        // Send mouse motion notify.
        memset(&event, 0, sizeof(event));
        event.type = MotionNotify;
        event.xmotion.window = target_window;
        event.xmotion.x = 100;
        event.xmotion.y = 100;
        XSendEvent(display, target_window, True, PointerMotionMask, &event);
        XFlush(display);
       
        // Send down key press and release.
        memset(&event, 0, sizeof(event));
        event.type = KeyPress;
        event.xkey.window = target_window;
        event.xkey.keycode = 116;
        XSendEvent(display, target_window, True, KeyPressMask, &event);
        XFlush(display);
        sleep(.2);
        memset(&event, 0, sizeof(event));
        event.type = KeyRelease;
        event.xkey.window = target_window;
        event.xkey.keycode = 116;
        XSendEvent(display, target_window, True, KeyReleaseMask, &event);
        XFlush(display);

        sleep(1);
        std::cout << "Finished core event test." << std::endl;
    }

    // Core/XI2 + Send event bit
    if (test_id == 1) {
        std::cout << "Running xi2 event test." << std::endl;
        sleep(1);
        int xi_opcode, first_event, error;
        if (!XQueryExtension(display, "XInputExtension", &xi_opcode, &first_event, &error)) {
            fprintf(stderr, "XInput extension not available\n");
            return 1;
        }


        // Set input focus.
        XSetInputFocus(display, target_window, RevertToParent, CurrentTime);
        XFlush(display);

        // Send enter notify.
        XEvent event;
        memset(&event, 0, sizeof(event));
        event.type = EnterNotify;
        event.xcrossing.window = target_window;
        event.xcrossing.root = root;
        event.xcrossing.subwindow = None;
        event.xcrossing.time = CurrentTime;
        event.xcrossing.x = 100;
        event.xcrossing.y = 100;
        event.xcrossing.x_root = 100;
        event.xcrossing.y_root = 100;
        event.xcrossing.mode = NotifyNormal;
        event.xcrossing.detail = NotifyNonlinear;
        event.xcrossing.same_screen = True;
        event.xcrossing.focus = True;
        event.xcrossing.state = 0;
        XSendEvent(display, target_window, True, EnterWindowMask, &event);
        XFlush(display);

        // Send focus in.
        memset(&event, 0, sizeof(event));
        event.type = FocusIn;
        event.xfocus.window = target_window;
        event.xfocus.mode = NotifyNormal;
        event.xfocus.detail = NotifyNonlinear;
        XSendEvent(display, target_window, True, FocusChangeMask, &event);
        XFlush(display);

        // Send xi mouse motion notify.
        int mouse_id = 2;  // Assuming the mouse device ID is 2
        int x = 100, y = 200;  // Coordinates for the mouse motion event

        XIDeviceEvent xi_event;
        memset(&xi_event, 0, sizeof(xi_event));
        xi_event.type = GenericEvent;
        xi_event.extension = xi_opcode;
        xi_event.evtype = XI_Motion;
        xi_event.deviceid = mouse_id;
        xi_event.detail = 0;
        xi_event.root = root;
        xi_event.event = target_window;
        xi_event.child = None;
        xi_event.root_x = x;
        xi_event.root_y = y;
        xi_event.event_x = x;
        xi_event.event_y = y;
        xi_event.flags = 0;
        xi_event.mods.base = 0;
        xi_event.mods.latched = 0;
        xi_event.mods.locked = 0;
        xi_event.mods.effective = 0;
        xi_event.time = CurrentTime;
        XSendEvent(display, target_window, True, 0, (XEvent *)&xi_event);
        XFlush(display);
       
        // Send down key press and release.
        int kb_id = 3;  // Assuming the keyboard device ID is 3

        XIDeviceEvent key_press_event, key_release_event;
        memset(&key_press_event, 0, sizeof(key_press_event));
        memset(&key_release_event, 0, sizeof(key_release_event));

        // Set common fields for both events
        key_press_event.type = GenericEvent;
        key_press_event.extension = xi_opcode;
        key_press_event.deviceid = kb_id;
        key_press_event.detail = XKeysymToKeycode(display, XK_Down);  // Key code for the "Down" arrow key
        key_press_event.root = root;
        key_press_event.event = target_window;
        key_press_event.child = None;
        key_press_event.root_x = 0;
        key_press_event.root_y = 0;
        key_press_event.event_x = 0;
        key_press_event.event_y = 0;
        key_press_event.flags = 0;
        key_press_event.mods.base = 0;
        key_press_event.mods.latched = 0;
        key_press_event.mods.locked = 0;
        key_press_event.mods.effective = 0;
        key_press_event.time = CurrentTime;

        // Set specific fields for key press event
        key_press_event.evtype = XI_KeyPress;

        // Set specific fields for key release event
        key_release_event = key_press_event;  // Copy common fields from key press event
        key_release_event.evtype = XI_KeyRelease;
        key_release_event.time = CurrentTime;  // Update the time for the key release event

        // Send key press event
        XSendEvent(display, target_window, True, 0, (XEvent *)&key_press_event);
        XFlush(display);

        // Send key release event
        XSendEvent(display, target_window, True, 0, (XEvent *)&key_release_event);
        XFlush(display);
        sleep(1);
        std::cout << "Finished xi2 event test." << std::endl;
    }

    // TODO: Core + no send event bit

    // TODO: Core/XI2 + no send event bit
}
