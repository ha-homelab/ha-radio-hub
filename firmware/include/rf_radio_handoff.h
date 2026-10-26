// Copyright (c) 2026 HA Radio Hub contributors. SPDX-License-Identifier: MIT
#pragma once
#include <cstdint>

namespace rf_bridge {
// CC1101 config registers use single read; status registers require burst-read.
// Transactions use the existing radio's SPI delegate and therefore its bus lock.
template<typename Radio> uint8_t read_cc1101(Radio &radio, uint8_t command) {
  radio.enable();
  radio.transfer_byte(command);
  const uint8_t result = radio.transfer_byte(0);
  radio.disable();
  return result;
}

template<typename Radio> bool cc1101_state(Radio &radio, uint8_t expected) {
  // MARCSTATE is a changing status register: require two agreeing reads.
  const uint8_t first = read_cc1101(radio, 0xF5) & 0x1F;
  const uint8_t second = read_cc1101(radio, 0xF5) & 0x1F;
  return first == expected && second == expected;
}

template<typename Radio, typename Transmitter> bool prepare_radio_tx(Radio &radio, Transmitter &tx) {
  if (radio.is_failed() || tx.is_failed())
    return false;
  tx.digital_write(true);
  if (tx.status_has_warning())
    return false;
  // IOCFG0=Hi-Z outside TX. GDO2 retains its independent async RX output.
  // In async TX the CC1101 automatically uses GDO0 as its data input.
  radio.enable();
  radio.transfer_byte(0x02);
  radio.transfer_byte(0x2E);
  radio.disable();
  if (read_cc1101(radio, 0x82) != 0x2E)
    return false;
  radio.set_idle();
  if (!cc1101_state(radio, 0x01))
    return false;
  // Low is safe after verified Hi-Z, and prevents a pull-up-created OOK carrier
  // while entering TX. Never start the waveform until TX is confirmed.
  tx.digital_write(false);
  if (tx.status_has_warning()) {
    tx.digital_write(true);
    return false;
  }
  radio.begin_tx();
  if (!cc1101_state(radio, 0x13) || read_cc1101(radio, 0x82) != 0x2E) {
    tx.digital_write(true);
    radio.set_idle();
    return false;
  }
  return true;
}

template<typename Radio, typename Transmitter>
bool finish_radio_tx(Radio &radio, Transmitter &tx, bool resume_rx) {
  radio.set_idle();
  const bool idle = cc1101_state(radio, 0x01);
  // A synchronous setup/carrier failure may leave no usable RMT channel.
  // Keep RX suspended and latch the fault without sending through that channel.
  if (tx.is_failed())
    return false;
  tx.digital_write(true);
  if (!idle || tx.status_has_warning() || read_cc1101(radio, 0x82) != 0x2E)
    return false;
  if (!resume_rx)
    return true;
  radio.begin_rx();
  return cc1101_state(radio, 0x0D);
}
}  // namespace rf_bridge
