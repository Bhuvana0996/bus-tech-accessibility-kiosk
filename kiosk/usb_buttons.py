import logging
import os
import time

log = logging.getLogger("kiosk.usb_buttons")

# Your custom 4-key keypad is programmed as:
#   KEY1 -> 0 -> Bus 191
#   KEY4 -> 1 -> Bus 400
#
# These can still be overridden with environment variables if needed.
BUTTON1_KEY = os.environ.get("BUTTON1_KEY", "KEY_0").upper()
BUTTON2_KEY = os.environ.get("BUTTON2_KEY", "KEY_1").upper()

# Optional exact Linux input device path, e.g.
# /dev/input/by-id/usb-...-event-kbd
BUTTON_DEVICE = os.environ.get("BUTTON_DEVICE", "").strip()


class USBButtonReader:
    """Reads Bus 191 / Bus 400 selection buttons from the custom USB keypad."""

    def __init__(self, callback):
        self.callback = callback
        self.running = True
        self.device = None

    def _open_device(self):
        from evdev import InputDevice

        if not BUTTON_DEVICE:
            return None

        try:
            device = InputDevice(BUTTON_DEVICE)
            log.info(
                "Using configured USB keypad: %s (%s)",
                device.name,
                device.path,
            )
            return device
        except Exception as exc:
            log.warning("Configured BUTTON_DEVICE unavailable: %s", exc)
            return None

    def _find_device(self):
        """
        Find the custom keypad.

        Priority:
        1. BUTTON_DEVICE exact path, when configured.
        2. The old known VID/PID (kept for compatibility).
        3. A small HID keypad exposing KEY_0 / KEY_1.

        The final fallback avoids normal full-size keyboards where possible.
        """

        from evdev import InputDevice, ecodes, list_devices

        # 1. Exact device path
        device = self._open_device()
        if device:
            return device

        # 2. Backwards-compatible VID/PID match
        old_vendor_id = 0x1189
        old_product_id = 0x8890

        candidates = []

        for path in list_devices():
            try:
                candidate = InputDevice(path)

                if (
                    candidate.info.vendor == old_vendor_id
                    and candidate.info.product == old_product_id
                ):
                    log.info(
                        "Found USB keypad by VID/PID: %s (%s)",
                        candidate.name,
                        candidate.path,
                    )
                    return candidate

                # Keep devices that expose both required keys.
                caps = candidate.capabilities().get(ecodes.EV_KEY, [])
                key_names = set()

                for code in caps:
                    try:
                        name = ecodes.KEY[code]
                        if isinstance(name, list):
                            key_names.update(name)
                        else:
                            key_names.add(name)
                    except Exception:
                        continue

                if BUTTON1_KEY in key_names and BUTTON2_KEY in key_names:
                    candidates.append((candidate, len(caps)))
                else:
                    candidate.close()

            except Exception:
                try:
                    candidate.close()
                except Exception:
                    pass

        # 3. Prefer the smallest key device, which is normally the 4-key keypad.
        if candidates:
            candidates.sort(key=lambda item: item[1])
            selected, key_count = candidates[0]

            # A normal keyboard typically has many more keys.
            log.info(
                "Found USB keypad by key capability: %s (%s), %s EV_KEY codes",
                selected.name,
                selected.path,
                key_count,
            )

            for other, _ in candidates[1:]:
                try:
                    other.close()
                except Exception:
                    pass

            return selected

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
                        log.info(
                            "USB keypad connected: %s (%s)",
                            self.device.name,
                            self.device.path,
                        )
                        log.info(
                            "Button mapping: %s=Bus 191, %s=Bus 400",
                            BUTTON1_KEY,
                            BUTTON2_KEY,
                        )
                    else:
                        time.sleep(2)
                        continue

                except Exception as exc:
                    log.warning("USB keypad unavailable: %s", exc)
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
                        log.info("KEY1 -> Bus 191")
                        self.callback("BUTTON1")

                    elif key == BUTTON2_KEY:
                        log.info("KEY4 -> Bus 400")
                        self.callback("BUTTON2")

            except Exception as exc:
                log.warning("USB keypad disconnected: %s", exc)

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
