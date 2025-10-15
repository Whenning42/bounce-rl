from dataclasses import dataclass

from Xlib.display import Display
from Xlib.xobject.drawable import Window


@dataclass
class WindowConnection:
    display: Display
    window: Window
