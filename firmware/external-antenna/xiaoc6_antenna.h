#pragma once
#include "esp_err.h"

/* Select the XIAO ESP32C6 U.FL path before starting any radio stack. */
esp_err_t xiaoc6_select_external_antenna(void);
