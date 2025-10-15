from dataclasses import dataclass

from Xlib.display import Display


@dataclass
class DisplayConnection:
    display: Display
