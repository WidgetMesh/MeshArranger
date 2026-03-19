#pragma once

#include <stdbool.h>
#include "esp_err.h"
#include "esp_netif.h"

#ifdef __cplusplus
extern "C" {
#endif

esp_err_t mp_usbnet_start(const char *hostname,
                          const char *ip,
                          const char *netmask,
                          const char *gateway);

esp_err_t mp_usbnet_stop(void);

bool mp_usbnet_is_up(void);

esp_netif_t *mp_usbnet_get_esp_netif(void);

#ifdef __cplusplus
}
#endif
