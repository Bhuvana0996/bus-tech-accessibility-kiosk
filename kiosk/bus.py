import glob
import logging
import os
import threading

log = logging.getLogger("kiosk.bus")


class BusPicoController:
    """Sends ramp/audio commands to the separate bus-side Pico over USB serial."""

    def __init__(self):
        self.lock = threading.Lock()

    def _find_port(self):
        configured = os.environ.get("BUS_PICO_PORT")
        if configured:
            return configured

        ports = sorted(glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"))
        kiosk_port = os.environ.get("PICO_PORT")
        for port in ports:
            if port != kiosk_port:
                return port
        return None

    def send(self, command):
        port = self._find_port()
        if not port:
            log.warning("Bus Pico not found; set BUS_PICO_PORT to its serial port")
            return False

        with self.lock:
            try:
                import serial
                ser = serial.Serial(port, 115200, timeout=1)
                ser.write((command.strip().upper() + "\n").encode("utf-8"))
                ser.flush()
                ser.close()
                log.info("Bus Pico command: %s", command)
                return True
            except Exception as exc:
                log.warning("Bus Pico unavailable at %s: %s", port, exc)
                return False
