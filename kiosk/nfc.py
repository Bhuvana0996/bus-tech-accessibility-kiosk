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

        log.info("Starting SPI...")
        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)

        # PN532 SPI chip-select: GPIO8 / physical pin 24 / SPI0 CE0.
        cs_pin = DigitalInOut(board.CE0)

        log.info("Initializing PN532 over SPI...")
        pn532 = PN532_SPI(spi, cs_pin, debug=False)

        log.info("Checking PN532 firmware...")
        ic, ver, rev, _ = pn532.firmware_version
        log.info("PN532 detected! IC=0x%02X firmware=%d.%d", ic, ver, rev)

        pn532.SAM_configuration()
        self.reader = pn532

    def run_forever(self):
        last_uid = None
        last_seen = 0.0

        while self.running:
            try:
                self._connect()
                log.info("PN532 ready. Tap an NFC card now.")

                while self.running:
                    # Poll for ISO14443A / NFC-A cards.  Keep the timeout
                    # short so the kiosk remains responsive when no card is present.
                    uid = self.reader.read_passive_target(
                        card_baud=106,
                        timeout=0.5,
                    )

                    if uid is None:
                        continue

                    card_id = "".join(f"{x:02X}" for x in uid)
                    uid_text = ":".join(f"{x:02X}" for x in uid)

                    now = time.monotonic()
                    if uid_text == last_uid and now - last_seen < 2.0:
                        continue

                    last_uid, last_seen = uid_text, now
                    log.info("TAG DETECTED! ID Number: %s", card_id)
                    self.callback(uid_text)

            except Exception as exc:
                log.warning("NFC unavailable: %s", exc)
                self.reader = None
                time.sleep(3)

    def stop(self):
        self.running = False
