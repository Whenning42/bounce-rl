#include "lib_mpx_input.h"

#include <X11/Xlib.h>
#include <X11/extensions/XInput2.h>
#include <X11/extensions/XTest.h>
#include <stdbool.h>
#include <string.h>

int get_cursor_id(Display* display, char* cursor_name) {
    int num_devices;
    char full_name[256];
    strcpy(full_name, cursor_name);
    strcat(full_name, " pointer");
    XIDeviceInfo* devices = XIQueryDevice(display, XIAllDevices, &num_devices);
    for (int i = 0; i < num_devices; i++) {
        if (strcmp(devices[i].name, full_name) == 0) {
            return devices[i].deviceid;
        }
    }
    return -1;
}

Display* open_display(char* display_name) {
    return XOpenDisplay(display_name);
}

void make_cursor(Display* display, Window client_connection_window, char* cursor_name) {
    XIAddMasterInfo add;
    add.type = XIAddMaster;
    add.name = cursor_name;
    add.send_core = True;
    add.enable = True;
    XIChangeHierarchy(display, (XIAnyHierarchyChangeInfo*)&add, 1);
    int device_id = get_cursor_id(display, cursor_name);
    XISetClientPointer(display, 0, device_id);
    XISetClientPointer(display, client_connection_window, device_id);
    XSync(display, False);
}

void delete_cursor(Display* display, char* cursor_name) {
    int cursor_id = get_cursor_id(display, cursor_name);
    if (cursor_id == -1) {
        return;
    }

    XIRemoveMasterInfo remove;
    remove.type = XIRemoveMaster;
    remove.deviceid = cursor_id;
    remove.return_mode = XIAttachToMaster;
    remove.return_pointer = 2;
    remove.return_keyboard = 3;
    XIChangeHierarchy(display, (XIAnyHierarchyChangeInfo*)&remove, 1);
    XSync(display, False);
} 

void key_event(Display* display, unsigned int keycode, bool is_press) {
    XTestFakeKeyEvent(display, keycode, is_press, 0);
    XFlush(display);
}

void move_mouse(Display* display, int x, int y) {
    XTestFakeMotionEvent(display, 0, x, y, 0);
    XFlush(display);
}

void button_event(Display* display, unsigned int button, bool is_press) {
    XTestFakeButtonEvent(display, button, is_press, 0);
    XFlush(display);
}

void xflush(Display* display) {
    XFlush(display);
}
