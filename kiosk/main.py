"""Entry point for the accessibility kiosk prototype."""

import tkinter as tk

from display import KioskDisplay


def main():
    root = tk.Tk()
    app = KioskDisplay(root)
    root.mainloop()


if __name__ == "__main__":
    main()
