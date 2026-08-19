"""7-inch LCD interface for the kiosk prototype.

The LCD is output only. Bus selection is intentionally handled by
physical buttons, not touchscreen buttons.
"""

import tkinter as tk


class KioskDisplay:
    def __init__(self, root):
        self.root = root
        self.root.title("Accessibility Transport Kiosk")
        self.root.geometry("1024x600")
        self.root.configure(bg="white")

        title = tk.Label(
            root,
            text="ACCESSIBILITY TRANSPORT KIOSK",
            font=("Arial", 28, "bold"),
            bg="white",
        )
        title.pack(pady=70)

        message = tk.Label(
            root,
            text="Please tap your NFC card to begin",
            font=("Arial", 24),
            bg="white",
        )
        message.pack(pady=30)

        note = tk.Label(
            root,
            text="Bus selection will be made using the physical bus clickers.",
            font=("Arial", 16),
            bg="white",
        )
        note.pack(pady=20)
