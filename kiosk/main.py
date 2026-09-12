#!/usr/bin/env python3
"""Raspberry Pi 5 hardware bridge for the Accessibility Kiosk."""

import asyncio
import logging
from pathlib import Path
from typing import Set

from aiohttp import web

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
        self.nfc = NFCReader(self.on_nfc)
        self.pico = PicoReader(self.on_button)

    def emit_from_thread(self, event, **data):
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self.broadcast(event, **data), self.loop
            )

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
            # Additional-assistance needs are sent to the UI for visual display only.
            # They are intentionally NOT spoken aloud or sent to the bus system.
            self.emit_from_thread(
                "nfc_registered",
                uid=uid,
                name=user["name"],
                accessibility=user.get("accessibility") or "Not specified",
            )
        else:
            self.emit_from_thread("nfc_unregistered", uid=uid)

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
                # The kiosk session is intentionally self-contained after arrival information.
                # The separate bus-side Pico is operated independently and does not receive
                # passenger accessibility data or automatic BOARD commands from this server.
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
        log.info("Kiosk UI: http://127.0.0.1:%s/index.html", PORT)

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
