"""Physical bus-button interface.

Hardware GPIO handling will be added after the LCD/UI prototype is tested.
For now this module defines the bus services used by the kiosk.
"""

BUS_SERVICES = {
    "BUS_12": "Bus 12",
    "BUS_27": "Bus 27",
    "BUS_36": "Bus 36",
}


def get_bus_name(bus_id: str) -> str:
    return BUS_SERVICES[bus_id]
