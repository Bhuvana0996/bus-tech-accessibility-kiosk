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

    def _try_pn532(self, spi, cs_pin, speed):
        from adafruit_pn532.spi import PN532_SPI

        # PN532 V4 can be sensitive to SPI speed depending on wiring/power.
        pn532 = PN532_SPI(spi, cs_pin, debug=False)

        # PN532_SPI configures the SPI bus itself when communicating.
        # Give the bus a conservative speed before the first command.
        deadline = time.monotonic() + 3
        while not spi.try_lock():
            if time.monotonic() >= deadline:
                raise RuntimeError("SPI bus could not be locked")
            time.sleep(0.02)
        try:
            spi.configure(baudrate=speed, polarity=0, phase=0, bits=8)
        finally:
            spi.unlock()

        ic, ver, rev, _ = pn532.firmware_version
        log.info(
            "PN532 detected! IC=0x%02X firmware=%d.%d at %d Hz",
            ic, ver, rev, speed
        )
        pn532.SAM_configuration()
        return pn532

    def _connect(self):
        import board
        import busio
        from digitalio import DigitalInOut

        log.info("Starting SPI...")
        self.spi = busio.SPI(board.SCK, board.MOSI, board.MISO)

        # The project wiring is:
        # MOSI=19, MISO=21, SCK=23, SS/CE0=24.
        self.cs_pin = DigitalInOut(board.CE0)
        self.cs_pin.switch_to_output(value=True)

        # Try conservative SPI speeds first. This is more tolerant of
        # breadboard/jumper-wire signal quality than a high clock rate.
        speeds = (100_000, 250_000, 500_000, 1_000_000)

        last_error = None
        for speed in speeds:
            for attempt in range(1, 4):
                if not self.running:
                    return

                try:
                    log.info(
                        "Checking PN532 over CE0 at %d Hz (attempt %d/3)...",
                        speed, attempt
                    )
                    pn532 = self._try_pn532(self.spi, self.cs_pin, speed)
                    self.reader = pn532
                    return
                except Exception as exc:
                    last_error = exc
                    log.warning(
                        "PN532 SPI check failed at %d Hz (attempt %d/3): %s",
                        speed, attempt, exc
                    )
                    time.sleep(0.5)

        raise RuntimeError(f"PN532 did not respond over SPI/CE0: {last_error}")

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
