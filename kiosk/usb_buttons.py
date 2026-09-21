import logging
import os
import time

log = logging.getLogger("kiosk.usb_buttons")

VENDOR_ID = 0x1189
PRODUCT_ID = 0x8890

BUTTON1_KEY = os.environ.get("BUTTON1_KEY", "KEY_1").upper()
BUTTON2_KEY = os.environ.get("BUTTON2_KEY", "KEY_2").upper()


class USBButtonReader:
    """Reads the two bus-selection buttons from the USB HID button panel."""

    def __init__(self, callback):
        self.callback = callback
        self.running = True
        self.device = None

    def _find_device(self):
        from evdev import InputDevice, list_devices

        for path in list_devices():
            try:
                device = InputDevice(path)
                if device.info.vendor == VENDOR_ID and device.info.product == PRODUCT_ID:
                    return device
                device.close()
            except Exception:
                continue
        return None

    def run_forever(self):
        try:
            from evdev import ecodes
        except Exception as exc:
            log.error("evdev unavailable: %s", exc)
            while self.running:
                time.sleep(5)
            return

        while self.running:
            if self.device is None:
                try:
                    self.device = self._find_device()
                    if self.device:
                        log.info("USB button panel connected: %s (%s)", self.device.name, self.device.path)
                        log.info("Button mapping: %s=Bus 191, %s=Bus 400", BUTTON1_KEY, BUTTON2_KEY)
                    else:
                        time.sleep(2)
                        continue
                except Exception as exc:
                    log.warning("USB button panel unavailable: %s", exc)
                    self.device = None
                    time.sleep(2)
                    continue

            try:
                for event in self.device.read_loop():
                    if not self.running:
                        break
                    if event.type != ecodes.EV_KEY or event.value != 1:
                        continue

                    key = ecodes.KEY[event.code]
                    if isinstance(key, list):
                        key = key[0]

                    if key == BUTTON1_KEY:
                        log.info("Keyboard 1 button 1 -> Bus 191")
                        self.callback("BUTTON1")
                    elif key == BUTTON2_KEY:
                        log.info("Keyboard 1 button 2 -> Bus 400")
                        self.callback("BUTTON2")
            except Exception as exc:
                log.warning("USB button panel disconnected: %s", exc)
                try:
                    self.device.close()
                except Exception:
                    pass
                self.device = None
                time.sleep(2)

    def stop(self):
        self.running = False
        if self.device:
            try:
                self.device.close()
            except Exception:
                pass
            self.device = None
