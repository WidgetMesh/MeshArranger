#pragma once

#include "esp_err.h"
#include "esp_netif.h"

#ifdef __cplusplus
extern "C" {
#endif

esp_err_t usb_netif_glue_start(esp_netif_t *netif);
esp_err_t usb_netif_glue_stop(void);

#ifdef __cplusplus
}
#endif
