import evdev
import threading
import time
from src.keyboard import ds4drv_input

class Controller():
    def __init__(self, callbacks=[], user = True):
        self.has_user = user
        if user:
            while len(evdev.list_devices()) < 1:
                print("Waiting for a controller to be plugged in.")
                time.sleep(5)
            self.user_device = evdev.InputDevice(evdev.list_devices()[0])
            self.user_device.grab()

        self.out_device = ds4drv_input.create_uinput_device("ds4")

        self.left_trigger = 0
        self.right_trigger = 0
        self.lstick = [0, 0]
        self.rstick = [0, 0]

        self.callbacks = callbacks
        self.user_locked = False

        # Environment controls
        self.pause_button = "BTN_NORTH"
        self.paused = False
        self.mark_done_button = "BTN_EAST"
        self.marked_done = False

        if user:
            self._start()

    def _start(self):
        t = threading.Thread(target=self.loop)
        t.start()

    def lock_user(self):
        self.user_locked = True

    def unlock_user(self):
        self.user_locked = False

    def inject(self, e_type, code, value, syn = True):
        self.out_device.write_event(e_type, code, value)
        if syn:
            self.out_device.device.syn()

    def apply_action(self, action):
        self.inject(3, evdev.ecodes.ABS_X, int(255 * (action[0] + .5)), syn = False)
        self.inject(3, evdev.ecodes.ABS_RX, int(255 * action[1]), syn = False)
        self.inject(3, evdev.ecodes.ABS_RY, int(255 * action[2]))

    def loop(self):
        if not self.has_user:
            return

        for e in self.user_device.read_loop():
            if e.type == evdev.ecodes.EV_ABS:
                v = evdev.ecodes.bytype[evdev.ecodes.EV_ABS][e.code]
                if v == "ABS_X":
                    # Adding 0.0 converts -0.0 to 0.0
                    self.lstick[0] = round(2 * e.value / 255 - 1, 2) + 0.0
                elif v == "ABS_Y":
                    self.lstick[1] = round(2 * e.value / 255 - 1, 2) + 0.0
                elif v == "ABS_Z":
                    self.rstick[0] = round(2 * e.value / 255 - 1, 2) + 0.0
                elif v == "ABS_RZ":
                    self.rstick[1] = round(2 * e.value / 255 - 1, 2) + 0.0
                elif v == "ABS_RX":
                    self.left_trigger = round(e.value / 255)
                elif v == "ABS_RY":
                    self.right_trigger = round(e.value / 255)

                for f in self.callbacks:
                    f(self, e)

            if not self.user_locked:
                self.out_device.write_event(e.type, e.code, e.value)
                self.out_device.device.syn()

            if e.type == evdev.ecodes.EV_KEY and e.value == 0:
                v = evdev.ecodes.bytype[evdev.ecodes.EV_KEY][e.code]
                if self.pause_button in v:
                    self.paused = not self.paused
                if self.mark_done_button in v:
                    self.marked_done = True

    def state(self):
        return {"ls_x": self.lstick[0],
                "ls_y": self.lstick[1],
                "rs_x": self.rstick[0],
                "rs_y": self.rstick[1],
                "lt": self.left_trigger,
                "rt": self.right_trigger}

    def __repr__(self):
        return f"lstick: {self.lstick}, rstick: {self.rstick}, lt: {self.left_trigger}, rt: {self.right_trigger})"

if __name__ == '__main__':
    controller = Controller()

    def print_cont(cont):
        print(cont.state())

    controller.register_callback(print_cont)
    controller.start()

