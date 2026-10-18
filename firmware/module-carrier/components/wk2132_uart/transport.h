#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>

namespace esphome::wk2132_uart {
// DFRobot WK2132 register protocol, UART1, 14.7456 MHz crystal.
// IO must implement bool reg_read/reg_write/fifo_read/fifo_write and pause().
enum class Fault : uint8_t { NONE, IO, IDENTITY, LINE, RX_OVERFLOW, TX_OVERFLOW, SETTINGS };
template<size_t N> class Ring {
 public:
  size_t size() const { return count_; }
  size_t free() const { return N - count_; }
  void clear() { head_ = count_ = 0; }
  void push(const uint8_t *p, size_t n) {
    for (size_t i = 0; i < n; ++i) data_[(head_ + count_ + i) % N] = p[i];
    count_ += n;
  }
  void peek(uint8_t *p, size_t n) const {
    for (size_t i = 0; i < n; ++i) p[i] = data_[(head_ + i) % N];
  }
  void drop(size_t n) { head_ = (head_ + n) % N; count_ -= n; }
 private:
  std::array<uint8_t, N> data_{};
  size_t head_{0}, count_{0};
};

template<size_t QueueSize=2048> class BasicTransport {
 public:
  static constexpr uint8_t GENA=0, GRST=1, SPAGE=3, SCR=4, LCR=5,
      FCR=6, SIER=7, TFCNT=9, RFCNT=10, FSR=11;
  static constexpr size_t FIFO=256, CHUNK=64, QUEUE=QueueSize;
  Fault fault() const { return fault_; }
  bool good() const { return fault_ == Fault::NONE; }
  bool idle() const { return tx_.size() == 0 && wire_idle_; }
  size_t available() const { return good() ? rx_.size() : 0; }
  size_t pending() const { return tx_.size(); }
  size_t tx_free() const { return tx_.free(); }
  void fail(Fault fault) { if (good()) fault_=fault; rx_.clear(); tx_.clear(); wire_idle_=false; }
  bool enqueue(const uint8_t *p, size_t n) {
    if (!good()) return false;
    if (n > tx_.free()) { fail(Fault::TX_OVERFLOW); return false; }
    tx_.push(p,n);
    if (n) wire_idle_=false;
    return true;
  }
  bool receive(uint8_t *p, size_t n, bool peek=false) {
    if (!good() || n > rx_.size()) return false;
    rx_.peek(p,n);
    if (!peek) rx_.drop(n);
    return true;
  }
  template<class IO> bool initialize(IO &io) {
    uint8_t identity;
    if (!io.reg_read(GENA,identity)) { fail(Fault::IO); return false; }
    if (!(identity & 0x80)) { fail(Fault::IDENTITY); return false; }
    // Disable the unused UART2, reset UART1, program while RX/TX are disabled.
    const uint8_t init[][2]={{GENA,1},{GRST,1},{SPAGE,0},{SCR,0},{SIER,0},
      {LCR,0},{FCR,0x0f},{SPAGE,1},{4,0},{5,7},{6,0}};
    for (const auto &r:init) {
      if (!io.reg_write(r[0],r[1])) { fail(Fault::IO); return false; }
      if (r[0]==GRST) io.pause();
    }
    for (const auto &r:std::array<std::array<uint8_t,2>,3>{{{{4,0}},{{5,7}},{{6,0}}}}) {
      uint8_t v;
      if (!io.reg_read(r[0],v)) { fail(Fault::IO); return false; }
      if (v!=r[1]) { fail(Fault::IDENTITY); return false; }
    }
    if (!io.reg_write(SPAGE,0) || !io.reg_write(SCR,3)) { fail(Fault::IO); return false; }
    return health(io);
  }
  template<class IO> bool health(IO &io) {
    const uint8_t expected[][3]={{GENA,0x83,0x81},{SPAGE,1,0},{SCR,7,3},{LCR,0x3f,0}};
    for (const auto &r:expected) {
      uint8_t v;
      if (!io.reg_read(r[0],v)) { fail(Fault::IO); return false; }
      if ((v&r[1])!=r[2]) { fail(Fault::IDENTITY); return false; }
    }
    return good();
  }
  template<class IO> void service(IO &io) {
    if (!good()) return;
    // Bounded work, alternating RX/TX. No other consumer or writer owns UART1.
    for (unsigned burst=0; burst<4 && good(); ++burst) {
      uint8_t count, status;
      if (!io.reg_read(RFCNT,count) || !io.reg_read(FSR,status)) { fail(Fault::IO); return; }
      if (status&0xf0) { fail(Fault::LINE); return; }
      size_t rx_count=count;
      if (count==0 && (status&8)) {
        // Data may have arrived between the count and flag reads. Only a second
        // zero count with data present denotes a full 256-byte hardware FIFO.
        if (!io.reg_read(RFCNT,count)) { fail(Fault::IO); return; }
        rx_count=count ? count : FIFO;
      }
      size_t n=std::min(rx_count,CHUNK);
      std::array<uint8_t,CHUNK> data{};
      if (n) {
        if (n>rx_.free()) { fail(Fault::RX_OVERFLOW); return; }
        if (!io.fifo_read(data.data(),n) || !io.reg_read(FSR,status)) { fail(Fault::IO); return; }
        if (status&0xf0) { fail(Fault::LINE); return; }
        rx_.push(data.data(),n);
      }
      if (!io.reg_read(TFCNT,count) || !io.reg_read(FSR,status)) { fail(Fault::IO); return; }
      if (status&0xf0) { fail(Fault::LINE); return; }
      // With one writer, an older count only underestimates free space.
      const size_t free=(status&2) ? 0 : FIFO-count;
      const size_t send=std::min({free,tx_.size(),CHUNK});
      wire_idle_=(status&7)==0;
      if (send) {
        tx_.peek(data.data(),send);
        // A NACK may follow partial transmission: never retry an ambiguous write.
        if (!io.fifo_write(data.data(),send)) { fail(Fault::IO); return; }
        tx_.drop(send);
        wire_idle_=false;
      }
      if (!n && !send) return;
    }
  }
 private:
  Ring<QUEUE> rx_, tx_;
  Fault fault_{Fault::NONE};
  bool wire_idle_{false};
};
using Transport = BasicTransport<>;
}  // namespace esphome::wk2132_uart
