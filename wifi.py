import network
import time

def wifi_reset():
    sta = network.WLAN(network.STA_IF)
    ap = network.WLAN(network.AP_IF)
    sta.active(False)
    ap.active(False)
    sta.active(True)
    sta.scan()
    
    # Optional: wait for it to be active
    while not sta.active():
        time.sleep(0.1)
    sta.disconnect() # For ESP8266
    
def connect_wifi(ssid, password):
    # Create a station network interface
    wlan = network.WLAN(network.STA_IF)
    
    # Activate the interface
    wlan.active(True)
    
    # Check if already connected to avoid re-connecting unnecessarily
    if not wlan.isconnected():
        print(f'Connecting to network: {ssid}...')
        wlan.connect(ssid, password)

        # Wait for connection with a timeout
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            print('.', end='')
            time.sleep(1)
            timeout -= 1
        
        if wlan.isconnected():
            print('\nConnection successful!')
        else:
            print('\nFailed to connect.')
            return None

    # Print the network configuration (IP address, netmask, gateway, DNS)
    print('Network config:', wlan.ifconfig())
    return wlan

# --- Example Usage ---
# Replace 'YOUR_SSID' and 'YOUR_PASSWORD' with your actual credentials
wifi_reset()
connect_wifi('Ruby', 'CanRobotsDream')
