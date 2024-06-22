# A python xlib sendevent input library.

import Xlib.display
import Xlib.protocol
import Xlib.X
import Xlib.XK
import Xlib.xobject


class LibSendEvent:
    def __init__(self, event_window: Xlib.xobject.drawable.Window):
        self.root = event_window.query_tree().root
        self.event_window = event_window
        self.last_rx = 0
        self.last_ry = 0
        self.last_wx = 0
        self.last_wy = 0

    def open_display(self, display_name: bytes) -> Xlib.display.Display:
        display_name = display_name.decode()
        # Xlib needs None instead of an empty string.
        if not display_name:
            display_name = None
        return Xlib.display.Display(display_name)

    def close_display(self, display) -> None:
        display.close()

    # LibMPX specific.
    def make_cursor(self, display, cursor_name) -> None:
        pass

    # LibMPX specific.
    def assign_cursor(self, display, client_connection_window, cursor_name) -> None:
        return None

    # LibMPX specific.
    def delete_cursor(self, display, cursor) -> None:
        return None

    def key_event(self, display, keycode, is_press) -> None:
        event_type = (
            Xlib.protocol.event.KeyPress if is_press else Xlib.protocol.event.KeyRelease
        )
        event = event_type(
            time=Xlib.X.CurrentTime,
            root=self.root,
            window=self.event_window,
            same_screen=1,
            child=Xlib.X.NONE,
            root_x=0,
            root_y=0,
            event_x=0,
            event_y=0,
            state=0,
            detail=keycode,
        )
        self.event_window.send_event(event, propagate=True)

    def move_mouse(self, display, x, y) -> None:
        tc = self.event_window.translate_coords(self.root, x, y)
        win_x, win_y = tc.x, tc.y
        event = Xlib.protocol.event.MotionNotify(
            time=Xlib.X.CurrentTime,
            root=self.root,
            window=self.event_window,
            same_screen=1,
            child=Xlib.X.NONE,
            root_x=x,
            root_y=y,
            event_x=win_x,
            event_y=win_y,
            state=0,
            detail=0,
        )
        self.event_window.send_event(event, propagate=True)
        self.last_rx = x
        self.last_ry = y
        self.last_wx = win_x
        self.last_wy = win_y

    def button_event(self, display, button, is_press) -> None:
        event_type = (
            Xlib.protocol.event.ButtonPress
            if is_press
            else Xlib.protocol.event.ButtonRelease
        )
        event = event_type(
            time=Xlib.X.CurrentTime,
            root=self.root,
            window=self.event_window,
            same_screen=1,
            child=Xlib.X.NONE,
            root_x=self.last_rx,
            root_y=self.last_ry,
            event_x=self.last_wx,
            event_y=self.last_wy,
            state=0,
            detail=button,
        )
        self.event_window.send_event(event, propagate=True)

    def xflush(self, display) -> None:
        display.flush()
