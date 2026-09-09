import glob
import logging
import os
import time

log = logging.getLogger("kiosk.pico")


class PicoReader:
    """Reads BUTTON1/BUTTON2 lines from a Raspberry Pi Pico over USB serial."""

    def __init__(self, callback):
        self.callback = callback
        self.running = True
        self.serial = None

    def _find_port(self):
        configured = os.environ.get("PICO_PORT")
        if configured:
            return configured
        ports = sorted(glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"))
        return ports[0] if ports else None

    def run_forever(self):
        while self.running:
            port = self._find_port()
            if not port:
                time.sleep(2)
                continue
            try:
                import serial
                log.info("Connecting to Pico at %s", port)
                self.serial = serial.Serial(port, 115200, timeout=1)
                log.info("Pico connected")
                while self.running:
                    raw = self.serial.readline()
                    if not raw:
                        continue
                    line = raw.decode("utf-8", errors="ignore").strip().upper()
                    if line in ("BUTTON1", "BUTTON2"):
                        log.info("Pico event: %s", line)
                        self.callback(line)
            except Exception as exc:
                log.warning("Pico unavailable: %s", exc)
                try:
                    if self.serial:
                        self.serial.close()
                except Exception:
                    pass
                self.serial = None
                time.sleep(2)

    def stop(self):
        self.running = False
        try:
            if self.serial:
                self.serial.close()
        except Exception:
            pass
