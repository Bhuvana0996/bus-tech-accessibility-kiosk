"""Visual interface for the 7-inch LCD.

The LCD is OUTPUT ONLY. Users select buses with physical bus clickers.
Keyboard keys 1, 2 and 3 simulate those clickers during development.
"""

import tkinter as tk


class KioskDisplay:
    def __init__(self, root):
        self.root = root
        self.controller = None
        self.root.title("Accessibility Transport Kiosk")
        self.root.geometry("1024x600")
        self.root.configure(bg="#F5F7FA")
        self.root.resizable(False, False)
        self.root.bind("<Key-1>", lambda _event: self._button("12"))
        self.root.bind("<Key-2>", lambda _event: self._button("27"))
        self.root.bind("<Key-3>", lambda _event: self._button("36"))

        self.header = tk.Label(
            root,
            text="ACCESSIBILITY TRANSPORT KIOSK",
            font=("Arial", 28, "bold"),
            bg="#F5F7FA",
            fg="#16324F",
        )
        self.header.pack(pady=(38, 18))

        self.content = tk.Frame(root, bg="#F5F7FA")
        self.content.pack(fill="both", expand=True)

        self.show_bus_selection()

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def show_bus_selection(self):
        self.clear_content()
        tk.Label(
            self.content,
            text="SELECT YOUR BUS SERVICE",
            font=("Arial", 25, "bold"),
            bg="#F5F7FA",
            fg="#16324F",
        ).pack(pady=(18, 28))

        for bus, key in [("12", "1"), ("27", "2"), ("36", "3")]:
            tk.Label(
                self.content,
                text=f"BUS {bus}    •    Press physical Bus {bus} clicker",
                font=("Arial", 20),
                bg="white",
                fg="#222222",
                padx=25,
                pady=15,
                relief="solid",
                bd=1,
            ).pack(fill="x", padx=120, pady=7)

        tk.Label(
            self.content,
            text="Development test: press keyboard 1, 2 or 3 to simulate the physical clickers.",
            font=("Arial", 14),
            bg="#F5F7FA",
            fg="#555555",
        ).pack(pady=20)

    def show_confirmation(self, bus):
        self.clear_content()
        tk.Label(
            self.content,
            text=f"BUS {bus} SELECTED",
            font=("Arial", 30, "bold"),
            bg="#F5F7FA",
            fg="#16324F",
        ).pack(pady=(45, 18))
        tk.Label(
            self.content,
            text=f"Would you like to proceed with Bus {bus}?",
            font=("Arial", 25),
            bg="#F5F7FA",
            fg="#222222",
        ).pack(pady=15)
        tk.Label(
            self.content,
            text=f"Press the Bus {bus} clicker AGAIN to confirm.\nPress a different bus clicker to choose another bus.",
            font=("Arial", 19),
            bg="#F5F7FA",
            fg="#444444",
            justify="center",
        ).pack(pady=25)

    def show_arrival(self, bus, info):
        self.clear_content()
        tk.Label(
            self.content,
            text=f"BUS {bus} CONFIRMED",
            font=("Arial", 30, "bold"),
            bg="#F5F7FA",
            fg="#16324F",
        ).pack(pady=(28, 8))
        tk.Label(
            self.content,
            text=info["destination"],
            font=("Arial", 22),
            bg="#F5F7FA",
            fg="#333333",
        ).pack(pady=5)
        tk.Label(
            self.content,
            text=f"Next arrival: {info['next']}",
            font=("Arial", 25, "bold"),
            bg="white",
            fg="#222222",
            padx=35,
            pady=20,
            relief="solid",
            bd=1,
        ).pack(fill="x", padx=180, pady=18)
        tk.Label(
            self.content,
            text=f"Following bus: {info['following']}",
            font=("Arial", 20),
            bg="#F5F7FA",
            fg="#333333",
        ).pack(pady=8)
        tk.Label(
            self.content,
            text="Assistance request can be added in the next project stage.",
            font=("Arial", 15),
            bg="#F5F7FA",
            fg="#666666",
        ).pack(pady=15)

    def _button(self, bus):
        if self.controller:
            self.controller.bus_pressed(bus)
