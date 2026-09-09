#!/usr/bin/env python3
"""Raspberry Pi 5 hardware bridge for the Accessibility Kiosk."""

import asyncio
import logging
from pathlib import Path
from typing import Set

from aiohttp import web

from audio import speak
from database import lookup_card
from nfc import NFCReader
from pico import PicoReader

ROOT = Path(__file__).resolve().parent.parent
PORT = 8000

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("kiosk")


class KioskServer:
    def __init__(self):
        self.clients: Set[web.WebSocketResponse] = set()
        self.loop = None
        self.language = "en"
        self.nfc = NFCReader(self.on_nfc)
        self.pico = PicoReader(self.on_button)

    def emit_from_thread(self, event, **data):
        if self.loop:
            asyncio.run_coroutine_threadsafe(self.broadcast(event, **data), self.loop)

    async def broadcast(self, event, **data):
        payload = {"event": event, **data}
        dead = []
        for ws in list(self.clients):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.clients.discard(ws)
        log.info("EVENT %s", payload)

    def on_nfc(self, uid):
        user = lookup_card(uid)
        if user:
            accessibility = user.get("accessibility") or "Not specified"
            self.emit_from_thread(
                "nfc_registered",
                uid=uid,
                name=user["name"],
                accessibility=accessibility,
            )
            speak(
                self.language,
                f"Hi {user['name']}. Your accessibility profile is {accessibility}. Please select your bus.",
            )
        else:
            self.emit_from_thread("nfc_unregistered", uid=uid)
            speak(self.language, "This card is not registered. Please contact LTA Customer Service at 1800 2255 582.")

    def on_button(self, button):
        self.emit_from_thread("button", button=button)

    async def ws_handler(self, request):
        ws = web.WebSocketResponse(heartbeat=20)
        await ws.prepare(request)
        self.clients.add(ws)
        await ws.send_json({"event": "backend_ready"})
        log.info("Kiosk UI connected")
        try:
            async for msg in ws:
                if msg.type != web.WSMsgType.TEXT:
                    continue
                try:
                    data = msg.json()
                except Exception:
                    continue
                event = data.get("event")
                if event == "language":
                    self.language = data.get("lang", "en")
                elif event == "select_bus":
                    bus = int(data.get("bus", 191))
                    texts = {
                        "en": f"Take Bus {bus}? Press the same physical button again to confirm.",
                        "zh": f"乘坐 {bus} 号巴士？请再次按下相同的实体按钮确认。",
                        "ms": f"Naik Bas {bus}? Tekan butang fizikal yang sama sekali lagi untuk mengesahkan.",
                        "ta": f"{bus} பேருந்தில் செல்லவா? உறுதிப்படுத்த அதே இயற்பியல் பொத்தானை மீண்டும் அழுத்தவும்。",
                    }
                    speak(self.language, texts.get(self.language, texts["en"]))
                elif event == "confirm_bus":
                    bus = int(data.get("bus", 191))
                    mins = 5 if bus == 191 else 8
                    texts = {
                        "en": f"Bus {bus} will arrive in {mins} minutes. Thank you for using our service.",
                        "zh": f"{bus}号巴士将在{mins}分钟后到达。感谢您使用我们的服务。",
                        "ms": f"Bas {bus} akan tiba dalam {mins} minit. Terima kasih kerana menggunakan perkhidmatan kami.",
                        "ta": f"{bus} பேருந்து {mins} நிமிடங்களில் வரும். எங்கள் சேவையைப் பயன்படுத்தியதற்கு நன்றி.",
                    }
                    speak(self.language, texts.get(self.language, texts["en"]))
        finally:
            self.clients.discard(ws)
        return ws

    async def health(self, request):
        return web.json_response({"ok": True, "service": "accessibility-kiosk"})

    async def run(self):
        self.loop = asyncio.get_running_loop()
        app = web.Application()
        app.add_routes([
            web.get("/ws", self.ws_handler),
            web.get("/health", self.health),
            web.static("/", str(ROOT), show_index=False),
        ])
        runner = web.AppRunner(app)
        await runner.setup()
        await web.TCPSite(runner, "127.0.0.1", PORT).start()
        log.info("Kiosk UI: http://127.0.0.1:%s/kiosk.html", PORT)

        nfc_task = asyncio.create_task(asyncio.to_thread(self.nfc.run_forever))
        pico_task = asyncio.create_task(asyncio.to_thread(self.pico.run_forever))
        try:
            await asyncio.gather(nfc_task, pico_task)
        finally:
            self.nfc.stop()
            self.pico.stop()
            await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(KioskServer().run())
    except KeyboardInterrupt:
        pass
