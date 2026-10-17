#pragma once
inline void zigbee_test_log(const char *, const char *, ...) {}
#define ESP_LOGI(...) zigbee_test_log(__VA_ARGS__)
#define ESP_LOGCONFIG(...) zigbee_test_log(__VA_ARGS__)
