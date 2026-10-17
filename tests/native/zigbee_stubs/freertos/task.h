#pragma once
#include "FreeRTOS.h"
// Tests invoke run_() on a joinable host thread; never start an RTOS task.
inline int xTaskCreate(void (*)(void *), const char *, uint32_t, void *, int, void *) { return pdPASS; }
inline void vTaskDelete(void *) {}
