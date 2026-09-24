import logging
import os
import time
from glob import glob

log = logging.getLogger("kiosk.usb_buttons")

# Custom 4-key keypad:
#   KEY1 sends 0 -> Bus 191
#   KEY4 sends 1 -> Bus 400
BUTTON1_KEY = os.environ.get("BUTTON1_KEY", "KEY_0").upper()
BUTTON2_KEY = os.environ.get("BUTTON2_KEY", "KEY_1").upper()
BUTTON_DEVICE = os.environ.get("BUTTON_DEVICE", "").strip()

# Linux may expose the same physical key under a keypad alias.
KEY_ALIASES = {
    "KEY_0": {"KEY_0", "KEY_KP0"},
    "KEY_1": {"KEY_1", "KEY_KP1"},
}

class USBButtonReader:
    """Reads KEY1/KEY4 from the custom USB HID keypad."""

    def __init__(self, callback):
        self.callback = callback
        self.running = True
        self.device = None
        log.info(
            "USB keypad reader starting; KEY1=%s -> Bus 191, KEY4=%s -> Bus 400",
            BUTTON1_KEY, BUTTON2_KEY
        )

    def _key_matches(self, key, configured):
        return key in KEY_ALIASES.get(configured, {configured})

    def _open_device(self, path):
        from evdev import InputDevice
        try:
            device = InputDevice(path)
            log.info("Opened input device: %s (%s)", device.name, device.path)
            return device
        except Exception as exc:
            log.debug("Could not open %s: %s", path, exc)
            return None

    def _find_device(self):
        from evdev import InputDevice, ecodes, list_devices

        # If explicitly configured, use it.
        if BUTTON_DEVICE:
            device = self._open_device(BUTTON_DEVICE)
            if device:
                return device

        # Check stable /dev/input/by-id paths first. This catches USB HID
        # keyboards/keypads even when event numbers change after reboot.
        preferred = []
        for path in sorted(glob("/dev/input/by-id/*")):
            if "-event-" in path:
                preferred.append(path)

        paths = preferred + [p for p in list_devices() if p not in preferred]
        log.info("Scanning %d Linux input device(s) for the USB keypad", len(paths))

        candidates = []

        for path in paths:
            candidate = None
            try:
                candidate = self._open_device(path)
                if not candidate:
                    continue

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
                    "Input device: name=%r path=%s vendor=%04x product=%04x",
                    candidate.name,
                    candidate.path,
                    candidate.info.vendor,
                    candidate.info.product,
                )

                # Legacy keypad VID/PID.
                if candidate.info.vendor == 0x1189 and candidate.info.product == 0x8890:
                    log.info("Matched keypad by legacy VID/PID: %s", candidate.path)
                    return candidate

                has_key1 = any(k in key_names for k in KEY_ALIASES.get(BUTTON1_KEY, {BUTTON1_KEY}))
                has_key4 = any(k in key_names for k in KEY_ALIASES.get(BUTTON2_KEY, {BUTTON2_KEY}))

                if has_key1 and has_key4:
                    candidates.append((candidate, len(caps)))
                else:
                    candidate.close()

            except Exception as exc:
                log.debug("Could not inspect input device %s: %s", path, exc)
                if candidate:
                    try:
                        candidate.close()
                    except Exception:
                        pass

        if candidates:
            candidates.sort(key=lambda item: item[1])
            selected, key_count = candidates[0]
            log.info(
                "USB keypad selected: %s (%s), %d EV_KEY codes",
                selected.name, selected.path, key_count
            )
            for other, _ in candidates[1:]:
                try:
                    other.close()
                except Exception:
                    pass
            return selected

        log.warning(
            "NO USB KEYPAD FOUND. Expected %s/%s (0/1) on a Linux EV_KEY device.",
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
                        log.info(
                            "USB KEYPAD CONNECTED: %s (%s)",
                            self.device.name, self.device.path
                        )
                        log.info(
                            "Key mapping active: KEY1=%s -> Bus 191 | KEY4=%s -> Bus 400",
                            BUTTON1_KEY, BUTTON2_KEY
                        )
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

                    names = ecodes.KEY[event.code]
                    if isinstance(names, list):
                        names = names[0]
                    key = names

                    log.info("USB keypad key event: %s", key)

                    if self._key_matches(key, BUTTON1_KEY):
                        log.info("KEY1 -> Bus 191")
                        self.callback("BUTTON1")
                    elif self._key_matches(key, BUTTON2_KEY):
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
