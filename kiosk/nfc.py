import logging
import time

log = logging.getLogger("kiosk.nfc")


class NFCReader:
    """ELECHOUSE PN532 V4 over SPI on Raspberry Pi 5."""

    def __init__(self, callback):
        self.callback = callback
        self.running = True
        self.reader = None
        self.spi = None
        self.cs_pin = None

    def _connect(self):
        import board
        import busio
        from digitalio import DigitalInOut
        from adafruit_pn532.spi import PN532_SPI

        # Make sure SPI is actually enabled before trying the PN532.
        log.info("Starting SPI...")
        self.spi = busio.SPI(board.SCK, board.MOSI, board.MISO)

        # Wait for the Linux SPI bus to become available.
        deadline = time.monotonic() + 5
        while not self.spi.try_lock():
            if time.monotonic() >= deadline:
                raise RuntimeError("SPI bus could not be locked")
            time.sleep(0.05)

        try:
            self.spi.configure(baudrate=1_000_000, polarity=0, phase=0, bits=8)
        finally:
            self.spi.unlock()

        self.cs_pin = DigitalInOut(board.CE0)
        self.cs_pin.switch_to_output(value=True)

        log.info("Initializing PN532 over SPI (CE0, 1 MHz)...")
        pn532 = PN532_SPI(self.spi, self.cs_pin, debug=False)

        # The PN532 can take a moment after power-up/reset before its
        # firmware command responds. Try several times instead of failing
        # the NFC reader permanently.
        last_error = None
        for attempt in range(1, 6):
            try:
                log.info("Checking PN532 firmware (attempt %d/5)...", attempt)
                ic, ver, rev, _ = pn532.firmware_version
                log.info(
                    "PN532 detected! IC=0x%02X firmware=%d.%d",
                    ic, ver, rev
                )

                pn532.SAM_configuration()
                self.reader = pn532
                return
            except Exception as exc:
                last_error = exc
                log.warning("PN532 check failed (attempt %d/5): %s", attempt, exc)
                time.sleep(0.8)

        raise RuntimeError(f"PN532 did not respond over SPI: {last_error}")

    def run_forever(self):
        last_uid = None
        last_seen = 0.0

        while self.running:
            try:
                self._connect()
                log.info("PN532 ready. Tap an NFC card now.")

                while self.running:
                    uid = self.reader.read_passive_target(timeout=0.5)

                    if uid is None:
                        continue

                    uid_text = ":".join(f"{x:02X}" for x in uid)
                    now = time.monotonic()
                    if uid_text == last_uid and now - last_seen < 2.0:
                        continue

                    last_uid, last_seen = uid_text, now
                    log.info(
                        "TAG DETECTED! ID Number: %s",
                        "".join(f"{x:02X}" for x in uid)
                    )
                    self.callback(uid_text)

            except Exception as exc:
                log.warning("NFC unavailable: %s", exc)
                self.reader = None
                time.sleep(3)

    def stop(self):
        self.running = False
        self.reader = None

        if self.cs_pin:
            try:
                self.cs_pin.value = True
                self.cs_pin.deinit()
            except Exception:
                pass

        self.cs_pin = None
        self.spi = None
