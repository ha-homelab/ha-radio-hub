#pragma once
#include "esp_err.h"

/* Call on every application boot, before initializing the 802.15.4 radio. */
esp_err_t tinyc6d_select_external_antenna(void);
