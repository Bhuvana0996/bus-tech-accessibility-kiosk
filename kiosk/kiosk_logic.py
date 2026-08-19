"""Core interaction logic for the physical bus clickers."""


class KioskController:
    """Implements the two-press confirmation flow.

    First press: select a bus.
    Same bus pressed again: confirm it.
    Different bus pressed: replace the pending selection.
    """

    def __init__(self, display, bus_services):
        self.display = display
        self.bus_services = bus_services
        self.pending_bus = None
        self.confirmed_bus = None

    def bus_pressed(self, bus):
        if self.confirmed_bus is not None:
            return

        if self.pending_bus is None:
            self.pending_bus = bus
            self.display.show_confirmation(bus)
            return

        if bus == self.pending_bus:
            self.confirmed_bus = bus
            self.display.show_arrival(bus, self.bus_services[bus])
            return

        # User changed their mind: start confirmation for the new bus.
        self.pending_bus = bus
        self.display.show_confirmation(bus)

    def reset(self):
        self.pending_bus = None
        self.confirmed_bus = None
        self.display.show_bus_selection()
