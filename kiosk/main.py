"""Main entry point for the accessibility kiosk prototype."""

import tkinter as tk

from display import KioskDisplay
from kiosk_logic import KioskController


BUS_SERVICES = {
    "12": {"next": "5 min", "following": "15 min", "destination": "HarbourFront"},
    "27": {"next": "3 min", "following": "13 min", "destination": "Tampines"},
    "36": {"next": "8 min", "following": "18 min", "destination": "Changi Airport"},
}


def main():
    root = tk.Tk()
    display = KioskDisplay(root)
    controller = KioskController(display, BUS_SERVICES)
    display.controller = controller
    root.mainloop()


if __name__ == "__main__":
    main()
