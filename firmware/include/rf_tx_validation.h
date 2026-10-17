// Copyright (c) 2026 RF Airbridge contributors. SPDX-License-Identifier: MIT
// Adapted from rf-airbridge c96777d0df65a7420e4883d79187f31eb1b98c9b.
#pragma once

#include <string>

namespace rf_bridge {

// Validate before indexing the protocol table or parsing a 64-bit RF value.
template<typename String>
inline bool valid_tx_request(const String &code, int protocol, int repeats) {
  if (code.size() < 8 || code.size() > 64 || protocol < 1 || protocol > 8 || repeats < 1 || repeats > 10)
    return false;
  for (char bit : code) {
    if (bit != '0' && bit != '1')
      return false;
  }
  return true;
}

// Check signed API values before the encoder narrows them to the 24/8/4/4-bit
// Dooya fields. The supplied check nibble is transmitted, not calculated here.
inline bool valid_dooya_request(int remote_id, int channel, int button, int check, int repeats) {
  return remote_id >= 0 && remote_id <= 0xFFFFFF && channel >= 0 && channel <= 0xFF && button >= 0 &&
         button <= 0x0F && check >= 0 && check <= 0x0F && repeats >= 1 && repeats <= 10;
}

}  // namespace rf_bridge
