#include "mp_usbnet.h"

#include <stdbool.h>
#include <string.h>

#include "esp_log.h"
#include "esp_netif_ip_addr.h"
#include "lwip/ip4_addr.h"
#include "usb_netif_glue.h"

// MicroPython headers are expected when this component is linked into
// the MicroPython ESP32 port build.
#include "py/obj.h"
#include "py/runtime.h"

static const char *TAG = "mp_usbnet";

static esp_netif_t *s_netif = NULL;
static bool s_up = false;

static esp_err_t set_static_ipv4(esp_netif_t *netif,
                                 const char *ip,
                                 const char *netmask,
                                 const char *gateway) {
    esp_netif_ip_info_t ip_info = {0};

    if (!ip4addr_aton(ip, &ip_info.ip) ||
        !ip4addr_aton(netmask, &ip_info.netmask) ||
        !ip4addr_aton(gateway, &ip_info.gw)) {
        return ESP_ERR_INVALID_ARG;
    }

    esp_err_t err = esp_netif_dhcpc_stop(netif);
    if (err != ESP_OK && err != ESP_ERR_ESP_NETIF_DHCP_ALREADY_STOPPED) {
        return err;
    }
    return esp_netif_set_ip_info(netif, &ip_info);
}

esp_err_t mp_usbnet_start(const char *hostname,
                          const char *ip,
                          const char *netmask,
                          const char *gateway) {
    if (s_up) {
        return ESP_OK;
    }

    if (!hostname || !ip || !netmask || !gateway) {
        return ESP_ERR_INVALID_ARG;
    }

    esp_netif_config_t cfg = ESP_NETIF_DEFAULT_ETH();
    s_netif = esp_netif_new(&cfg);
    if (!s_netif) {
        return ESP_FAIL;
    }

    esp_err_t err = esp_netif_set_hostname(s_netif, hostname);
    if (err != ESP_OK) {
        goto fail;
    }

    err = set_static_ipv4(s_netif, ip, netmask, gateway);
    if (err != ESP_OK) {
        goto fail;
    }

    err = usb_netif_glue_start(s_netif);
    if (err != ESP_OK) {
        goto fail;
    }

    s_up = true;
    ESP_LOGI(TAG, "USB netif started hostname=%s ip=%s", hostname, ip);
    return ESP_OK;

fail:
    if (s_netif) {
        esp_netif_destroy(s_netif);
        s_netif = NULL;
    }
    return err;
}

esp_err_t mp_usbnet_stop(void) {
    if (!s_up) {
        return ESP_OK;
    }

    esp_err_t err = usb_netif_glue_stop();
    if (err != ESP_OK) {
        return err;
    }
    if (s_netif) {
        esp_netif_destroy(s_netif);
        s_netif = NULL;
    }

    s_up = false;
    return ESP_OK;
}

bool mp_usbnet_is_up(void) {
    return s_up;
}

esp_netif_t *mp_usbnet_get_esp_netif(void) {
    return s_netif;
}

// ---- MicroPython module bindings ----

STATIC mp_obj_t mp_usbnet_start_py(size_t n_args, const mp_obj_t *args) {
    const char *hostname = mp_obj_str_get_str(args[0]);
    const char *ip = mp_obj_str_get_str(args[1]);
    const char *netmask = mp_obj_str_get_str(args[2]);
    const char *gateway = mp_obj_str_get_str(args[3]);

    esp_err_t err = mp_usbnet_start(hostname, ip, netmask, gateway);
    if (err != ESP_OK) {
        mp_raise_msg_varg(&mp_type_RuntimeError,
                          MP_ERROR_TEXT("usbnet start failed: %d"),
                          err);
    }
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(mp_usbnet_start_obj, 4, 4, mp_usbnet_start_py);

STATIC mp_obj_t mp_usbnet_stop_py(void) {
    esp_err_t err = mp_usbnet_stop();
    if (err != ESP_OK) {
        mp_raise_msg_varg(&mp_type_RuntimeError,
                          MP_ERROR_TEXT("usbnet stop failed: %d"),
                          err);
    }
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(mp_usbnet_stop_obj, mp_usbnet_stop_py);

STATIC mp_obj_t mp_usbnet_is_up_py(void) {
    return mp_obj_new_bool(mp_usbnet_is_up());
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(mp_usbnet_is_up_obj, mp_usbnet_is_up_py);

STATIC const mp_rom_map_elem_t mp_usbnet_globals_table[] = {
    {MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_usbnet)},
    {MP_ROM_QSTR(MP_QSTR_start), MP_ROM_PTR(&mp_usbnet_start_obj)},
    {MP_ROM_QSTR(MP_QSTR_stop), MP_ROM_PTR(&mp_usbnet_stop_obj)},
    {MP_ROM_QSTR(MP_QSTR_is_up), MP_ROM_PTR(&mp_usbnet_is_up_obj)},
};

STATIC MP_DEFINE_CONST_DICT(mp_usbnet_globals, mp_usbnet_globals_table);

const mp_obj_module_t mp_module_usbnet = {
    .base = {&mp_type_module},
    .globals = (mp_obj_dict_t *)&mp_usbnet_globals,
};

MP_REGISTER_MODULE(MP_QSTR_usbnet, mp_module_usbnet);
