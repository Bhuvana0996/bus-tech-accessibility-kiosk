"""Core kiosk interaction logic.

A bus must be selected twice to confirm it:
1. First press selects a bus and asks for confirmation.
2. Pressing the same bus again confirms it.
3. Pressing a different bus changes the pending selection.
"""


class KioskState:
    SELECTING = "selecting"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"


class KioskLogic:
    def __init__(self):
        self.state = KioskState.SELECTING
        self.pending_bus = None
        self.confirmed_bus = None

    def press_bus(self, bus_id: str):
        if self.state == KioskState.CONFIRMED:
            return {"action": "already_confirmed", "bus": self.confirmed_bus}

        if self.state == KioskState.SELECTING:
            self.pending_bus = bus_id
            self.state = KioskState.CONFIRMING
            return {"action": "confirm", "bus": bus_id}

        # We are waiting for confirmation. A different bus starts a new
        # confirmation cycle; the same bus confirms the selection.
        if bus_id == self.pending_bus:
            self.confirmed_bus = bus_id
            self.state = KioskState.CONFIRMED
            return {"action": "confirmed", "bus": bus_id}

        self.pending_bus = bus_id
        return {"action": "confirm", "bus": bus_id}

    def reset(self):
        self.state = KioskState.SELECTING
        self.pending_bus = None
        self.confirmed_bus = None
