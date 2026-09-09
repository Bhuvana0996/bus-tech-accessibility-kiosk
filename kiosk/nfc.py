import logging
import time

log = logging.getLogger("kiosk.nfc")


class NFCReader:
    """ELECHOUSE PN532 V4 over SPI on Raspberry Pi 5."""

    def __init__(self, callback):
        self.callback = callback
        self.running = True
        self.reader = None

    def _connect(self):
        import board
        import busio
        from digitalio import DigitalInOut
        from adafruit_pn532.spi import PN532_SPI

        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        cs_pin = DigitalInOut(board.CE0)  # GPIO8 / physical pin 24
        pn532 = PN532_SPI(spi, cs_pin, debug=False)
        ic, ver, rev, _ = pn532.firmware_version
        log.info("PN532 detected: IC=0x%02X firmware=%d.%d", ic, ver, rev)
        pn532.SAM_configuration()
        self.reader = pn532

    def run_forever(self):
        last_uid = None
        last_seen = 0.0
        while self.running:
            try:
                self._connect()
                log.info("NFC reader ready; waiting for card")
                while self.running:
                    uid = self.reader.read_passive_target(timeout=0.5)
                    if uid is None:
                        continue
                    uid_text = ":".join(f"{b:02X}" for b in uid)
                    now = time.monotonic()
                    if uid_text == last_uid and now - last_seen < 2.0:
                        continue
                    last_uid, last_seen = uid_text, now
                    log.info("NFC card UID: %s", uid_text)
                    self.callback(uid_text)
            except Exception as exc:
                log.warning("NFC unavailable: %s", exc)
                self.reader = None
                time.sleep(3)

    def stop(self):
        self.running = False
