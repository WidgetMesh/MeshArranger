"""Startup script for MicroPython gateway device."""

import uasyncio as asyncio

import rest_server

try:
    import usbnet
except ImportError:
    usbnet = None


def bring_up_usb_network():
    if usbnet is None:
        return

    if usbnet.is_up():
        return

    usbnet.start(
        "mesh-gateway",
        "192.168.137.2",
        "255.255.255.0",
        "192.168.137.1",
    )


async def main():
    bring_up_usb_network()
    await rest_server.main(host="0.0.0.0", port=8080)


asyncio.run(main())
