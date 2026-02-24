# MicroPython App

Files:

- `main.py`: startup entrypoint; brings up `usbnet` then starts REST server.
- `rest_server.py`: async REST service on port `8080`.

## Dependencies

- `uasyncio`
- `microdot_asyncio` (Microdot)

Install Microdot on the board filesystem before running.
