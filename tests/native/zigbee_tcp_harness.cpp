// Compile the actual ESPHome component with a bounded FIFO/CTS model and real
// loopback TCP. This is not a substitute for IDF or electrical validation.
#include "zigbee_tcp.cpp"
#undef bind
#undef select
#undef send
#undef recv
#include <chrono>
#include <csignal>
#include <deque>
#include <exception>
#include <iostream>
#include <mutex>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

using namespace std::chrono_literals;
namespace esphome { std::atomic<uint32_t> test_now{0}; }
static std::atomic<bool> stop_worker{false};
static std::atomic<uint16_t> bound_port{0};
static std::atomic<unsigned> send_calls{0}, recv_calls{0};
static std::atomic<bool> constrain_network{false};

static void require(bool condition, const std::string &message) {
  if (!condition) throw std::runtime_error(message);
}
template<class Predicate> static void until(Predicate predicate, const char *message) {
  const auto deadline = std::chrono::steady_clock::now() + 8s;
  while (!predicate()) {
    require(std::chrono::steady_clock::now() < deadline, message);
    std::this_thread::sleep_for(1ms);
  }
}

struct UartModel {
  std::mutex mutex;
  bool installed{false}, cts{true}, fail_install{false};
  unsigned installs{0}, deletes{0}, flushes{0}, blocked_writes{0}, tx_polls{0};
  std::deque<uint8_t> tx, rx;
  std::vector<uint8_t> wire;
  void drain() {
    if (cts) {
      wire.insert(wire.end(), tx.begin(), tx.end());
      tx.clear();
    }
  }
} uart;
static std::unique_lock<std::mutex> uart_lock() { return std::unique_lock(uart.mutex); }
bool uart_is_driver_installed(uart_port_t port) {
  require(port == UART_NUM_1, "unexpected UART");
  auto lock = uart_lock(); return uart.installed;
}
esp_err_t uart_param_config(uart_port_t, const uart_config_t *config) {
  require(config->baud_rate == 115200 && config->data_bits == UART_DATA_8_BITS &&
          config->parity == UART_PARITY_DISABLE && config->stop_bits == UART_STOP_BITS_1 &&
          config->flow_ctrl == UART_HW_FLOWCTRL_CTS_RTS, "UART must remain 115200 8N1 RTS/CTS");
  return ESP_OK;
}
esp_err_t uart_set_pin(uart_port_t, int tx, int rx, int rts, int cts) {
  require(tx == 17 && rx == 18 && rts == 16 && cts == 21, "UART pin contract changed");
  return ESP_OK;
}
esp_err_t uart_driver_install(uart_port_t, int rx_size, int tx_size, int, void *, int) {
  auto lock = uart_lock();
  require(rx_size == 4096 && tx_size == 0, "uart_tx_chars requires unbuffered TX");
  if (uart.fail_install) return ESP_FAIL;
  require(!uart.installed, "driver installed twice without delete");
  uart.installed = true; uart.installs++;
  // IDF driver initialization resets both hardware FIFOs.
  uart.tx.clear(); uart.rx.clear();
  return ESP_OK;
}
esp_err_t uart_driver_delete(uart_port_t) {
  auto lock = uart_lock();
  require(uart.installed, "deleted an uninstalled driver");
  uart.installed = false; uart.deletes++;
  return ESP_OK;
}
esp_err_t uart_flush_input(uart_port_t) {
  auto lock = uart_lock(); uart.rx.clear(); uart.flushes++;
  // Deliberately preserve TX, matching the real RX-only IDF API.
  return ESP_OK;
}
int uart_tx_chars(uart_port_t, const char *data, uint32_t size) {
  auto lock = uart_lock();
  require(uart.installed, "TX on an uninstalled UART");
  uart.drain();
  const size_t count = std::min<size_t>({size, 7, 128 - uart.tx.size()});
  for (size_t i = 0; i < count; i++) uart.tx.push_back(static_cast<uint8_t>(data[i]));
  if (!count) uart.blocked_writes++;
  uart.drain();
  return static_cast<int>(count);
}
esp_err_t uart_wait_tx_done(uart_port_t, TickType_t ticks) {
  require(ticks == 0, "worker must never block waiting for CTS");
  auto lock = uart_lock(); uart.drain(); uart.tx_polls++;
  return uart.tx.empty() ? ESP_OK : ESP_ERR_TIMEOUT;
}
int uart_read_bytes(uart_port_t, void *data, uint32_t size, TickType_t ticks) {
  require(ticks == 0, "worker must poll UART without a blocking read");
  auto lock = uart_lock();
  const size_t count = std::min<size_t>(size, uart.rx.size());
  auto *bytes = static_cast<uint8_t *>(data);
  for (size_t i = 0; i < count; i++) { bytes[i] = uart.rx.front(); uart.rx.pop_front(); }
  return static_cast<int>(count);
}
int zigbee_test_bind(int fd, const sockaddr *address, socklen_t size) {
  const int result = ::bind(fd, address, size);
  if (result == 0) {
    sockaddr_in actual{}; socklen_t actual_size = sizeof(actual);
    require(getsockname(fd, reinterpret_cast<sockaddr *>(&actual), &actual_size) == 0, "getsockname");
    bound_port = ntohs(actual.sin_port);
  }
  return result;
}
int zigbee_test_select(int count, fd_set *read, fd_set *write, fd_set *error, timeval *timeout) {
  if (stop_worker) { errno = EIO; return -1; }
  return ::select(count, read, write, error, timeout);
}
ssize_t zigbee_test_send(int fd, const void *data, size_t size, int flags) {
  if (constrain_network) {
    if (++send_calls % 3 == 0) { errno = EAGAIN; return -1; }
    size = std::min<size_t>(size, 31);
  }
  return ::send(fd, data, size, flags);
}
ssize_t zigbee_test_recv(int fd, void *data, size_t size, int flags) {
  if (constrain_network) {
    if (++recv_calls % 5 == 0) { errno = EAGAIN; return -1; }
    size = std::min<size_t>(size, 29);
  }
  return ::recv(fd, data, size, flags);
}

class Worker : public esphome::zigbee_tcp::ZigbeeTCP {
 public:
  void run() { run_(); }
};
class Fixture {
 public:
  Worker component;
  std::atomic<bool> done{false};
  std::exception_ptr error;
  std::thread thread;
  std::vector<int> clients;
  Fixture() {
    component.set_pins(17, 18, 16, 21); component.set_port(0); component.setup();
    require(!component.is_failed(), "component setup failed");
    thread = std::thread([this] {
      try { component.run(); } catch (...) { error = std::current_exception(); }
      done = true;
    });
    until([] { return bound_port.load() != 0; }, "server did not bind");
  }
  ~Fixture() {
    stop_worker = true;
    if (thread.joinable()) thread.join();
    for (int fd : clients) if (fd >= 0) ::close(fd);
  }
  int connect_client() {
    int fd = -1;
    until([&] {
      fd = ::socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
      require(fd >= 0, "client socket");
      sockaddr_in address{}; address.sin_family = AF_INET;
      address.sin_addr.s_addr = htonl(INADDR_LOOPBACK); address.sin_port = htons(bound_port);
      if (::connect(fd, reinterpret_cast<sockaddr *>(&address), sizeof(address)) == 0) return true;
      ::close(fd); return false;
    }, "client could not connect");
    require(fcntl(fd, F_SETFL, O_NONBLOCK) == 0, "nonblocking client");
    clients.push_back(fd); return fd;
  }
  void close_client(int fd) {
    ::shutdown(fd, SHUT_RDWR); ::close(fd);
    *std::find(clients.begin(), clients.end(), fd) = -1;
  }
  void check_error() {
    if (done && error) std::rethrow_exception(error);
  }
};
static void send_all(int fd, const std::vector<uint8_t> &data) {
  size_t offset = 0;
  until([&] {
    const ssize_t count = ::send(fd, data.data() + offset, data.size() - offset, 0);
    if (count > 0) offset += static_cast<size_t>(count);
    else require(count < 0 && (errno == EAGAIN || errno == EWOULDBLOCK || errno == EINTR), "client send failed");
    return offset == data.size();
  }, "client send timeout");
}
static std::vector<uint8_t> pattern(size_t size, uint8_t seed) {
  std::vector<uint8_t> data(size);
  for (size_t i = 0; i < size; i++) data[i] = static_cast<uint8_t>(i * 37 + seed);
  return data;
}
static bool client_closed(int fd) {
  uint8_t byte{};
  const ssize_t count = ::recv(fd, &byte, 1, MSG_PEEK);
  return count == 0 || (count < 0 && (errno == ECONNRESET || errno == ENOTCONN));
}
static void duplex() {
  constrain_network = true;
  Fixture fixture; int client = fixture.connect_client();
  const auto outgoing = pattern(4097, 0x23), incoming = pattern(5003, 0x91);
  send_all(client, outgoing);
  until([&] { auto lock = uart_lock(); return !uart.wire.empty(); }, "client not accepted");
  { auto lock = uart_lock(); uart.rx.insert(uart.rx.end(), incoming.begin(), incoming.end()); }
  std::vector<uint8_t> received;
  until([&] {
    uint8_t bytes[307]; const ssize_t count = ::recv(client, bytes, sizeof(bytes), 0);
    if (count > 0) received.insert(received.end(), bytes, bytes + count);
    else require(count < 0 && (errno == EAGAIN || errno == EWOULDBLOCK || errno == EINTR), "duplex read failed");
    auto lock = uart_lock(); return received.size() == incoming.size() && uart.wire.size() == outgoing.size();
  }, "duplex bytes lost or stalled");
  { auto lock = uart_lock(); require(uart.wire == outgoing, "TCP to UART bytes reordered/lost"); }
  require(received == incoming, "UART to TCP bytes reordered/lost");
  require(send_calls > 3 && recv_calls > 5, "partial network I/O/retry paths untested");
  fixture.check_error();
}
static void exclusive() {
  Fixture fixture; int first = fixture.connect_client(); send_all(first, {0x11});
  until([] { auto lock = uart_lock(); return uart.wire.size() == 1; }, "first client not accepted");
  int second = fixture.connect_client();
  until([&] { return client_closed(second); }, "second client was not rejected");
  send_all(first, {0x22});
  until([] { auto lock = uart_lock(); return uart.wire.size() == 2; }, "rejected client disturbed owner");
  fixture.close_client(first);
  until([] { auto lock = uart_lock(); return uart.deletes == 1; }, "disconnect did not reset UART");
  int third = fixture.connect_client(); send_all(third, {0x33});
  until([] { auto lock = uart_lock(); return uart.wire.size() == 3; }, "reconnect failed");
  { auto lock = uart_lock(); require(uart.wire == std::vector<uint8_t>({0x11, 0x22, 0x33}), "wrong client bytes"); }
  fixture.check_error();
}
static void session_fifo() {
  { auto lock = uart_lock(); uart.cts = false; }
  Fixture fixture; int first = fixture.connect_client(); send_all(first, {1, 2, 3, 4});
  until([] { auto lock = uart_lock(); return uart.tx.size() == 4; }, "old FIFO bytes missing");
  fixture.close_client(first);
  until([] { auto lock = uart_lock(); return uart.installs == 2; }, "disconnect did not reinitialize UART");
  { auto lock = uart_lock(); require(uart.tx.empty(), "old TX FIFO retained after disconnect"); uart.cts = true; }
  int second = fixture.connect_client(); send_all(second, {8, 9});
  until([] { auto lock = uart_lock(); return uart.wire.size() >= 2; }, "new session not transmitting");
  { auto lock = uart_lock(); require(uart.wire == std::vector<uint8_t>({8, 9}), "old session bytes escaped into new session"); }
  fixture.check_error();
}
static void blocked_timeout(bool software_pending, bool wraparound) {
  const uint32_t start = wraparound ? 0xFFFFFF00u : 100;
  esphome::test_now = start;
  { auto lock = uart_lock(); uart.cts = false; }
  Fixture fixture; int first = fixture.connect_client();
  send_all(first, pattern(software_pending ? 512 : 8, 0x41));
  until([&] {
    auto lock = uart_lock(); return software_pending ? uart.blocked_writes > 0 : uart.tx.size() == 8;
  }, "CTS stall not reached");
  unsigned polls;
  { auto lock = uart_lock(); polls = uart.tx_polls; }
  // Observe a later worker iteration before jumping the fake clock; otherwise
  // the final successful uart_tx_chars() may not yet have refreshed its timer.
  until([&] { auto lock = uart_lock(); return uart.tx_polls > polls; }, "worker did not poll stalled FIFO");
  esphome::test_now = start + 4999u;
  std::this_thread::sleep_for(40ms);
  { auto lock = uart_lock(); require(uart.deletes == 0, "timed out before five seconds"); }
  require(!client_closed(first), "client closed before timeout");
  esphome::test_now = start + 5000u;
  until([] { auto lock = uart_lock(); return uart.installs == 2; }, "CTS-stalled session never released");
  until([&] { return client_closed(first); }, "timed-out client remains open");
  { auto lock = uart_lock(); require(uart.tx.empty(), "timed-out FIFO not reset"); uart.cts = true; }
  int second = fixture.connect_client(); send_all(second, {0xA5});
  until([] { auto lock = uart_lock(); return !uart.wire.empty(); }, "new session refused after timeout");
  { auto lock = uart_lock(); require(uart.wire == std::vector<uint8_t>({0xA5}), "stalled old bytes transmitted after timeout"); }
  fixture.check_error();
}
static void idle() {
  Fixture fixture; int client = fixture.connect_client(); send_all(client, {1});
  until([] { auto lock = uart_lock(); return uart.wire.size() == 1; }, "first byte missing");
  esphome::test_now = 60000;
  std::this_thread::sleep_for(30ms);
  require(!client_closed(client), "healthy idle session was disconnected");
  send_all(client, {2});
  until([] { auto lock = uart_lock(); return uart.wire.size() == 2; }, "idle session lost UART access");
  { auto lock = uart_lock(); require(uart.deletes == 0, "idle session reset UART"); }
  fixture.check_error();
}
static void reset_failure() {
  Fixture fixture; int client = fixture.connect_client(); send_all(client, {1});
  until([] { auto lock = uart_lock(); return uart.wire.size() == 1; }, "client not accepted");
  { auto lock = uart_lock(); uart.fail_install = true; }
  fixture.close_client(client);
  until([&] { return fixture.done.load(); }, "failed UART reset did not stop worker");
  fixture.check_error(); fixture.component.loop();
  require(fixture.component.is_failed(), "reset fault was not exposed to ESPHome");
}
int main(int argc, char **argv) {
  std::signal(SIGPIPE, SIG_IGN);
  try {
    require(argc == 2, "one scenario required");
    const std::string scenario = argv[1];
    if (scenario == "duplex") duplex();
    else if (scenario == "exclusive") exclusive();
    else if (scenario == "session_fifo") session_fifo();
    else if (scenario == "software_timeout") blocked_timeout(true, false);
    else if (scenario == "fifo_timeout") blocked_timeout(false, false);
    else if (scenario == "wraparound") blocked_timeout(true, true);
    else if (scenario == "idle") idle();
    else if (scenario == "reset_failure") reset_failure();
    else require(false, "unknown scenario");
    std::cout << scenario << " PASS\n";
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n'; return 1;
  }
}
