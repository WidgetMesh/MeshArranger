# mp_usbnet_plugin

ESP-IDF 5.5 component intended for MicroPython ESP32-S3 firmware builds.

## What it provides

- MicroPython module: `usbnet`
- API:
  - `usbnet.start(hostname, ip, netmask, gateway)`
  - `usbnet.stop()`
  - `usbnet.is_up()`
- Creates an `esp_netif` object and applies static IPv4 config.
- Hook point for TinyUSB USB-NIC to lwIP packet bridge in `usb_netif_glue.c`.

## Status

- Module registration and control path are implemented.
- USB packet TX/RX bridge is a TODO and must be implemented for your selected USB class (ECM/NCM/RNDIS).

## Integration notes

1. Add this component to your ESP-IDF project components path.
2. Ensure MicroPython external module headers are visible in component include paths.
3. Add TinyUSB device configuration for USB network class.
4. Implement `usb_netif_glue_start/stop` with callbacks that push received USB frames into lwIP and send lwIP output to USB IN endpoint.
5. In your MicroPython startup script, call:

```python
import usbnet
usbnet.start("mesh-gateway", "192.168.137.2", "255.255.255.0", "192.168.137.1")
```

6. Start mDNS in firmware (or MicroPython layer) with hostname `mesh-gateway.local`.
