import logging
import time

log = logging.getLogger("kiosk.nfc")


class NFCReader:
    """PN532 V4 over SPI using Raspberry Pi CE0."""

    def __init__(self, callback):
        self.callback = callback
        self.running = True
        self.reader = None
        self.spi = None
        self.cs_pin = None

    def _close_connection(self):
        self.reader = None
        if self.cs_pin is not None:
            try:
                self.cs_pin.value = True
            except Exception:
                pass
            try:
                self.cs_pin.deinit()
            except Exception:
                pass
        if self.spi is not None:
            try:
                self.spi.unlock()
            except Exception:
                pass
        self.cs_pin = None
        self.spi = None

    def _connect(self):
        import board
        import busio
        from digitalio import DigitalInOut
        from adafruit_pn532.spi import PN532_SPI

        self._close_connection()
        log.info("Starting PN532 SPI on CE0...")

        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        cs_pin = DigitalInOut(board.CE0)
        cs_pin.switch_to_output(value=True)

        try:
            # Let the PN532 library own the SPI transaction settings.
            # 500 kHz is deliberately conservative for PN532 V4 boards.
            while not spi.try_lock():
                time.sleep(0.01)
            spi.configure(baudrate=500000, polarity=0, phase=0)
            spi.unlock()

            pn532 = PN532_SPI(spi, cs_pin, debug=False)

            # PN532_SPI() already performs the firmware detection internally.
            # Do not query firmware a second time: some PN532 V4 boards can
            # answer the first SPI transaction but miss the immediate second
            # one, which incorrectly caused the reader to be discarded.
            time.sleep(0.15)
            log.info("PN532 detected and SPI connection established.")

            pn532.SAM_configuration()

            self.spi = spi
            self.cs_pin = cs_pin
            self.reader = pn532

        except Exception:
            try:
                cs_pin.value = True
            except Exception:
                pass
            try:
                cs_pin.deinit()
            except Exception:
                pass
            try:
                spi.unlock()
            except Exception:
                pass
            self.spi = None
            self.cs_pin = None
            self.reader = None
            raise

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

                    last_uid = uid_text
                    last_seen = now

                    log.info(
                        "TAG DETECTED! ID Number: %s",
                        "".join(f"{x:02X}" for x in uid)
                    )
                    self.callback(uid_text)

            except Exception as exc:
                log.warning("NFC unavailable: %s", exc)
                self._close_connection()
                if self.running:
                    time.sleep(2)

    def stop(self):
        self.running = False
        self._close_connection()
