"""Visual interface for the 7-inch LCD.

The LCD is OUTPUT ONLY. Users select buses with physical bus clickers.
Keyboard keys 1, 2 and 3 simulate those clickers during development.

The visual language is inspired by the clear, high-contrast style of
Singapore public-transport self-service kiosks, without using SimplyGo
branding or assets.
"""

import tkinter as tk


class KioskDisplay:
    BG = "#EAF3F8"
    NAVY = "#17324D"
    GREEN = "#2E9E44"
    GREEN_DARK = "#247D36"
    WHITE = "#FFFFFF"
    TEXT = "#17324D"
    MUTED = "#5E7182"
    BORDER = "#C9D7E0"
    WARNING = "#FFF4D6"

    def __init__(self, root):
        self.root = root
        self.controller = None
        self.root.title("Accessibility Transport Kiosk")
        self.root.geometry("1024x600")
        self.root.configure(bg=self.BG)
        self.root.resizable(False, False)

        self.root.bind("<Key-1>", lambda _event: self._button("12"))
        self.root.bind("<Key-2>", lambda _event: self._button("27"))
        self.root.bind("<Key-3>", lambda _event: self._button("36"))

        header = tk.Frame(root, bg=self.NAVY, height=74)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="ACCESSIBILITY TRANSPORT KIOSK",
            font=("Arial", 24, "bold"),
            bg=self.NAVY,
            fg=self.WHITE,
        ).pack(side="left", padx=28, pady=20)

        self.content = tk.Frame(root, bg=self.BG)
        self.content.pack(fill="both", expand=True, padx=45, pady=25)

        self.show_bus_selection()

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def _title(self, text):
        tk.Label(
            self.content,
            text=text,
            font=("Arial", 28, "bold"),
            bg=self.BG,
            fg=self.TEXT,
        ).pack(pady=(8, 8))

    def _subtitle(self, text):
        tk.Label(
            self.content,
            text=text,
            font=("Arial", 17),
            bg=self.BG,
            fg=self.MUTED,
        ).pack(pady=(0, 18))

    def show_bus_selection(self):
        self.clear_content()
        self._title("Select your bus service")
        self._subtitle("Use the physical bus clicker for the service you want.")

        for bus in ["12", "27", "36"]:
            card = tk.Frame(
                self.content,
                bg=self.WHITE,
                highlightbackground=self.BORDER,
                highlightthickness=1,
            )
            card.pack(fill="x", pady=6)

            tk.Label(
                card,
                text=f"BUS {bus}",
                font=("Arial", 21, "bold"),
                bg=self.WHITE,
                fg=self.TEXT,
                anchor="w",
            ).pack(side="left", padx=22, pady=13)

            tk.Label(
                card,
                text=f"Physical Bus {bus} clicker",
                font=("Arial", 14),
                bg=self.WHITE,
                fg=self.MUTED,
            ).pack(side="right", padx=22)

        tk.Label(
            self.content,
            text="Prototype test: keyboard 1 / 2 / 3 simulates the physical clickers.",
            font=("Arial", 13),
            bg=self.BG,
            fg=self.MUTED,
        ).pack(pady=12)

    def show_confirmation(self, bus):
        self.clear_content()
        self._title(f"Bus {bus} selected")
        self._subtitle(f"Would you like to proceed with Bus {bus}?")

        box = tk.Frame(
            self.content,
            bg=self.WHITE,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        box.pack(fill="x", pady=10, ipady=10)

        tk.Label(
            box,
            text=f"Press the Bus {bus} clicker AGAIN to confirm.",
            font=("Arial", 21, "bold"),
            bg=self.WHITE,
            fg=self.GREEN_DARK,
        ).pack(pady=(18, 8))

        tk.Label(
            box,
            text="Press a different bus clicker if you want to change your selection.",
            font=("Arial", 16),
            bg=self.WHITE,
            fg=self.MUTED,
        ).pack(pady=(0, 18))

    def show_arrival(self, bus, info):
        self.clear_content()
        self._title(f"Bus {bus} confirmed")
        self._subtitle(info["destination"])

        cards = tk.Frame(self.content, bg=self.BG)
        cards.pack(fill="x", pady=4)

        for label, value in [("NEXT ARRIVAL", info["next"]), ("FOLLOWING BUS", info["following"])]:
            card = tk.Frame(
                cards,
                bg=self.WHITE,
                highlightbackground=self.BORDER,
                highlightthickness=1,
            )
            card.pack(side="left", expand=True, fill="both", padx=8, ipady=12)
            tk.Label(card, text=label, font=("Arial", 14, "bold"), bg=self.WHITE, fg=self.MUTED).pack(pady=(8, 2))
            tk.Label(card, text=value, font=("Arial", 29, "bold"), bg=self.WHITE, fg=self.GREEN_DARK).pack(pady=5)

        notice = tk.Frame(self.content, bg=self.WARNING)
        notice.pack(fill="x", pady=18)
        tk.Label(
            notice,
            text="Assistance request can be added in the next project stage.",
            font=("Arial", 16, "bold"),
            bg=self.WARNING,
            fg=self.TEXT,
        ).pack(pady=13)

    def _button(self, bus):
        if self.controller:
            self.controller.bus_pressed(bus)
