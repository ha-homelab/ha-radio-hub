#pragma once
#include <cstddef>
#include <cstdint>

namespace esphome::sc16is752_uart {
// Register numbers before SPI command encoding. Only channel A is supported.
enum Register : uint8_t { FIFO=0, IER=1, FCR=2, LCR=3, MCR=4, LSR=5,
                         SPR=7, TXLVL=8, RXLVL=9, IOCONTROL=14, EFCR=15 };
constexpr uint8_t command(uint8_t reg, bool read) { return (reg << 3) | (read ? 0x80 : 0); }
constexpr uint16_t divisor(uint32_t crystal, uint32_t baud) {
  return baud && crystal % (16ULL * baud) == 0 && crystal / (16ULL * baud) <= 65535
      ? static_cast<uint16_t>(crystal / (16ULL * baud)) : 0;
}

// Small transport-independent core: tested against a register/FIFO device model.
template<class IO> bool initialize(IO &io, uint32_t crystal, uint32_t baud) {
  const uint16_t div = divisor(crystal, baud);
  if (!div) return false;
  io.write(IOCONTROL, 0x08);  // resets both channels: no second component on this IC
  io.pause();
  io.write(LCR, 0x03);
  io.write(SPR, 0x5a);
  if (io.read(SPR) != 0x5a) return false;
  io.write(SPR, 0xa5);
  if (io.read(SPR) != 0xa5) return false;
  io.write(IER, 0);
  io.write(LCR, 0xbf);
  io.write(FCR, 0x10);  // EFR enhanced register; no software/RTS/CTS flow control
  io.write(LCR, 0x03);
  io.write(MCR, 0);     // divide-by-1 prescaler
  io.write(EFCR, 0);    // normal full duplex, TX and RX enabled
  io.write(LCR, 0x80);
  io.write(FIFO, div & 0xff);  // DLL bank
  io.write(IER, div >> 8);    // DLH bank
  io.write(LCR, 0x03);
  io.write(FCR, 0x07);  // FIFO enable + RX/TX reset
  io.write(FCR, 0x01);  // default eight-byte RX IRQ trigger + RX timeout IRQ
  io.write(IER, 0x05);  // RX available/timeout and RX line status; no TX IRQ storm
  return io.read(LCR) == 0x03;
}

// Returns false on a damaged stream: never silently forward corrupt Z-Wave bytes.
template<class IO, class RX, class TX> bool service(IO &io, RX receive, TX transmit) {
  if (io.read(LSR) & 0x9e) return false;  // FIFO error, break, framing, parity, overrun
  uint8_t count = io.read(RXLVL);
  if (count > 64) return false;
  for (uint8_t i=0; i<count; ++i) {
    // A bad byte may be behind good bytes in the FIFO; inspect every head byte.
    if (io.read(LSR) & 0x9e) return false;
    if (!receive(io.read(FIFO))) return false;
  }
  count = io.read(TXLVL);
  if (count > 64) return false;
  for (uint8_t i=0; i<count; ++i) {
    uint8_t value;
    if (!transmit(value)) break;
    io.write(FIFO, value);
  }
  return true;
}
}  // namespace esphome::sc16is752_uart
