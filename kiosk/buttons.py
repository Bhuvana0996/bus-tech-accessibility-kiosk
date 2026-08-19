"""Physical bus-button mapping.

Hardware GPIO will be connected later. During development, keyboard keys
1, 2 and 3 simulate these physical bus clickers.
"""

BUS_BUTTONS = {
    "12": 1,
    "27": 2,
    "36": 3,
}


def get_bus_from_button(button_number: int):
    for bus, button in BUS_BUTTONS.items():
        if button == button_number:
            return bus
    return None
