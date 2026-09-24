import logging
import os
import time

log = logging.getLogger("kiosk.usb_buttons")

# Custom 4-key keypad:
#   KEY1 sends 0 -> Bus 191
#   KEY4 sends 1 -> Bus 400
BUTTON1_KEY = os.environ.get("BUTTON1_KEY", "KEY_0").upper()
BUTTON2_KEY = os.environ.get("BUTTON2_KEY", "KEY_1").upper()
BUTTON_DEVICE = os.environ.get("BUTTON_DEVICE", "").strip()

class USBButtonReader:
    """Reads the two bus-selection keys from the custom USB HID keypad."""

    def __init__(self, callback):
        self.callback = callback
        self.running = True
        self.device = None
        log.info("USB keypad reader starting; expected %s=Bus 191, %s=Bus 400",
                 BUTTON1_KEY, BUTTON2_KEY)
        if BUTTON_DEVICE:
            log.info("BUTTON_DEVICE is set to: %s", BUTTON_DEVICE)

    def _open_device(self):
        from evdev import InputDevice
        if not BUTTON_DEVICE:
            return None
        try:
            device = InputDevice(BUTTON_DEVICE)
            log.info("Opened configured keypad: %s (%s)", device.name, device.path)
            return device
        except Exception as exc:
            log.warning("Could not open BUTTON_DEVICE %s: %s", BUTTON_DEVICE, exc)
            return None

    def _find_device(self):
        from evdev import InputDevice, ecodes, list_devices

        configured = self._open_device()
        if configured:
            return configured

        paths = list_devices()
        log.info("Scanning %d Linux input device(s) for the USB keypad", len(paths))

        candidates = []

        for path in paths:
            candidate = None
            try:
                candidate = InputDevice(path)
                caps = candidate.capabilities().get(ecodes.EV_KEY, [])
                key_names = set()

                for code in caps:
                    try:
                        names = ecodes.KEY[code]
                        if isinstance(names, list):
                            key_names.update(names)
                        else:
                            key_names.add(names)
                    except Exception:
                        pass

                log.info(
                    "Input device: name=%r path=%s vendor=%04x product=%04x keys=%s",
                    candidate.name,
                    candidate.path,
                    candidate.info.vendor,
                    candidate.info.product,
                    sorted(key_names)[:30],
                )

                # Exact legacy device ID, if this keypad uses it.
                if candidate.info.vendor == 0x1189 and candidate.info.product == 0x8890:
                    log.info("Matched keypad by legacy VID/PID: %s", candidate.path)
                    return candidate

                # The actual keypad is expected to expose KEY_0 and KEY_1.
                if BUTTON1_KEY in key_names and BUTTON2_KEY in key_names:
                    candidates.append((candidate, len(caps)))
                else:
                    candidate.close()

            except Exception as exc:
                log.warning("Could not inspect input device %s: %s", path, exc)
                if candidate:
                    try:
                        candidate.close()
                    except Exception:
                        pass

        if candidates:
            candidates.sort(key=lambda item: item[1])
            selected, key_count = candidates[0]
            log.info("Selected keypad: %s (%s), %d EV_KEY codes",
                     selected.name, selected.path, key_count)
            for other, _ in candidates[1:]:
                try:
                    other.close()
                except Exception:
                    pass
            return selected

        log.warning(
            "NO USB KEYPAD FOUND. Expected Linux keys %s and %s. "
            "If the keypad appears in lsusb but not here, check /dev/input permissions.",
            BUTTON1_KEY, BUTTON2_KEY
        )
        return None

    def run_forever(self):
        try:
            from evdev import ecodes
        except Exception as exc:
            log.exception("evdev cannot be imported: %s", exc)
            while self.running:
                time.sleep(5)
            return

        while self.running:
            if self.device is None:
                try:
                    self.device = self._find_device()
                    if self.device:
                        log.info("USB KEYPAD CONNECTED: %s (%s)",
                                 self.device.name, self.device.path)
                        log.info("Key mapping: KEY1=%s -> Bus 191 | KEY4=%s -> Bus 400",
                                 BUTTON1_KEY, BUTTON2_KEY)
                    else:
                        time.sleep(2)
                        continue
                except Exception as exc:
                    log.exception("USB keypad scan failed: %s", exc)
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

                    log.info("USB keypad key event: %s", key)

                    if key == BUTTON1_KEY:
                        log.info("KEY1 -> Bus 191")
                        self.callback("BUTTON1")
                    elif key == BUTTON2_KEY:
                        log.info("KEY4 -> Bus 400")
                        self.callback("BUTTON2")

            except Exception as exc:
                log.warning("USB keypad disconnected/read error: %s", exc)
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
