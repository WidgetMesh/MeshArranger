"""MicroPython REST server for mesh gateway.

This file targets MicroPython and uses uasyncio + Microdot.
"""

import time

import uasyncio as asyncio
from microdot_asyncio import Microdot, Response

try:
    import network
except ImportError:
    network = None

APP_VERSION = "1.0.0"
APP_NAME = "mesh-gateway"
DEVICE_IP = "192.168.137.2"
app = Microdot()
Response.default_content_type = "application/json"
START_TICKS = time.ticks_ms()


def _current_ip():
    if network is None:
        return "0.0.0.0"

    sta = network.WLAN(network.STA_IF)
    try:
        cfg = sta.ifconfig()
        return cfg[0]
    except Exception:
        return DEVICE_IP


def _status_payload():
    return {
        "uptime_ms": time.ticks_diff(time.ticks_ms(), START_TICKS),
        "ip": _current_ip(),
        "hostname": "mesh-gateway.local",
    }


@app.get("/health")
async def health(_req):
    return {"ok": True, "service": APP_NAME, "version": APP_VERSION}


@app.post("/echo")
async def echo(req):
    body = req.json or {}
    return {"ok": True, "echo": body.get("message", "")}


@app.post("/command")
async def command(req):
    body = req.json or {}
    cmd = body.get("cmd")
    args = body.get("args", {})

    if cmd == "status":
        return {"ok": True, "result": _status_payload()}

    if cmd == "echo":
        return {"ok": True, "result": {"echo": args.get("message", "")}}

    return {"ok": False, "error": "unknown_command", "cmd": cmd}


async def main(host="0.0.0.0", port=8080):
    await app.start_server(host=host, port=port)


if __name__ == "__main__":
    asyncio.run(main())
