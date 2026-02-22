#include "usb_netif_glue.h"

#include <stdbool.h>

#include "esp_log.h"

static const char *TAG = "usb_netif_glue";
static bool s_running = false;

esp_err_t usb_netif_glue_start(esp_netif_t *netif) {
    if (!netif) {
        return ESP_ERR_INVALID_ARG;
    }
    if (s_running) {
        return ESP_OK;
    }

    // TODO: Attach TinyUSB ECM/RNDIS RX/TX callbacks to lwIP netif.
    // This is hardware/stack specific and depends on your selected USB class.
    ESP_LOGI(TAG, "usb netif glue start (TODO packet bridge)");
    s_running = true;
    return ESP_OK;
}

esp_err_t usb_netif_glue_stop(void) {
    if (!s_running) {
        return ESP_OK;
    }

    // TODO: De-register TinyUSB callbacks and tear down queues.
    ESP_LOGI(TAG, "usb netif glue stop");
    s_running = false;
    return ESP_OK;
}
