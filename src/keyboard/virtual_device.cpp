// Note: XGrabKeyboard appears not to work for ourkeyboard forwarding needs.
// The file virtual_keyboard2.cpp in the git repo history contains details.

// Config trade-offs:
// - Manual Config (Use for now)
//     - User provides the keyboard device regex
// - Detect
//     can use this command to print all $master ($device) pairs:
//     $ xinput test-xi2 --root | grep --line-buffered "device" | grep -oP --line-buffered "\d.*" | awk '!x[$0]++'

#include "virtual_device.h"

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/extensions/XInput2.h>
#include <X11/extensions/XTest.h>
#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <array>
#include <cassert>
#include <vector>

std::string exec(const std::string& cmd) {
  std::array<char, 128> buffer;
  std::string result;
  FILE *pipe = popen(cmd.c_str(), "r");
  assert(pipe);
  while (!feof(pipe)) {
    if (fgets(buffer.data(), 128, pipe) != nullptr) {
      result += buffer.data();
    }
  }
  return result;
}

// Setup:
//   # User should configure this string.
//   $ KEYBOARD_REGEX="AT TRANSLATED"
//   $ xinput --create-master Bounce
//   $ MASTER_POINTER=$(xinput | grep "master pointer" | head -n1 | grep -oP "id=\K\d*")
//   $ MASTER_KEYBOARD=$(xinput | grep "master keyboard" | head -n1 | grep -oP "id=\K\d*")
//   $ DEVICE_KEYBOARD=$(xinput | grep "$KEYBOARD_REGEX" | grep -oP "id=\K\d*")
Devices SetUp() {
  std::string mp = exec(
      R"(xinput | grep "master pointer" | head -n1 | grep -oP "id=\K\d*")");
  if (mp.empty()) {
    std::cout << "Failed to find a master pointer" << std::endl;
    assert(false);
  }
  std::string mk = exec(
      R"(xinput | grep "master keyboard" | head -n1 | grep -oP "id=\K\d*")");
  if (mk.empty()) {
    std::cout << "Failed to find a master keyboard" << std::endl;
    assert(false);
  }
  std::string dk = exec(R"(xinput | grep ")" + kKeyboardRegex +
                        R"(" | grep -oP "id=\K\d*")");
  if (dk.empty()) {
    std::cout << "Failed to find a slave keyboard matching the user-specified "
                 "keyboard regex (regex:"
              << kKeyboardRegex << ")." << std::endl;
    assert(false);
  }

  return Devices{
      .master_pointer = std::stoi(mp),
      .master_keyboard = std::stoi(mk),
      .device_keyboard = std::stoi(dk)};
}

UserKeyboard::~UserKeyboard() {
  running_ = false;
  loop_.join();
  exec(R"(xinput --remove-master Bounce AttachToMaster ")" +
       std::to_string(devices_.master_pointer) + " " +
       std::to_string(devices_.master_keyboard) + R"(")");
}

UserKeyboard::UserKeyboard() {
  devices_ = SetUp();
  loop_ = std::thread(&UserKeyboard::StartLoop, this);
}

void UserKeyboard::StartLoop() {
  int device_keyboard = devices_.device_keyboard;
  Display *display = XOpenDisplay(NULL);
  Window win = DefaultRootWindow(display);

  std::vector<XIEventMask> masks;
  masks.resize(1);
  XIEventMask *m = &masks.back();
  m->deviceid = XIAllMasterDevices;
  m->mask_len = XIMaskLen(XI_LASTEVENT);
  m->mask = (unsigned char *)calloc(m->mask_len, sizeof(char));

  XISetMask(m->mask, XI_KeyPress);
  XISetMask(m->mask, XI_KeyRelease);
  // XISetMask(m->mask, XI_Motion);

  XISelectEvents(display, win, &masks[0], masks.size());

  XFlush(display);
  XIGrabDevice(display, device_keyboard, win, CurrentTime, None, GrabModeAsync,
               GrabModeAsync, False, m);
  // Warp the unused pointer offscreen.
  XIWarpPointer(display, devices_.master_pointer, None, None, 0, 0, 0, 0, 1920, 1080);
  XSync(display, False);

  while (running_) {
    XEvent ev;
    XGenericEventCookie *cookie = (XGenericEventCookie *)&ev.xcookie;
    XNextEvent(display, (XEvent *)&ev);

    if (XGetEventData(display, cookie) && cookie->type == GenericEvent) {
      if (cookie->evtype == XI_KeyPress) {
        XIDeviceEvent& dev = *(XIDeviceEvent*)cookie->data;
        std::cout << "keypress:  " << dev.detail << std::endl;
        if (disabled_) {
          continue;
        }
        if (dev.detail < 256) { // Should always be true?
          key_state_[dev.detail] = 1;
        } else {
          std::cout << "Unexpected keypress detail: " << dev.detail;
        }
        XTestFakeKeyEvent(display, dev.detail, true, CurrentTime);
      }
      if (cookie->evtype == XI_KeyRelease) {
        XIDeviceEvent& dev = *(XIDeviceEvent*)cookie->data;
        std::cout << "keyrelease:  " << dev.detail << std::endl;
        if (dev.detail < 256) { // Should always be true?
          key_state_[dev.detail] = 0;
        } else {
          std::cout << "Unexpected keyrelease detail: " << dev.detail;
        }
        XTestFakeKeyEvent(display, dev.detail, false, CurrentTime);
      }
    }
    XFreeEventData(display, cookie);
  }
}
