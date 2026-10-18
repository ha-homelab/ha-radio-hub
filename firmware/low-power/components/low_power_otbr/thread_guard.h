#pragma once
#include <cstdint>
#include <cstring>

namespace esphome::low_power_otbr {
// Plain data shared with host fault-injection tests. NVS owns integrity checking.
enum class ThreadFault : uint32_t {
  NONE, STORAGE, UART, SILENT_RCP, PROTOCOL, CAPABILITIES, API_VERSION,
  RESET_FAILED, INCOMPATIBLE, START_TIMEOUT, STACK_ERROR, HOST_CRASH, MAINTENANCE,
};
struct ThreadRecord {
  uint32_t magic{0x54485232};
  uint32_t armed{0};
  uint32_t quarantined{0};
  uint32_t fault{0};
  uint32_t faults{0};
  uint32_t retries{0};
};
inline bool valid_record(const ThreadRecord &r) {
  return r.magic == 0x54485232 && r.armed <= 1 && r.quarantined <= 1 &&
         r.fault <= static_cast<uint32_t>(ThreadFault::MAINTENANCE);
}
template<typename Write, typename Commit, typename Read>
bool write_verified_record(const ThreadRecord &record, Write write, Commit commit, Read read) {
  if (!write(record) || !commit()) return false;
  ThreadRecord check{};
  return read(check) && std::memcmp(&check, &record, sizeof(record)) == 0;
}
inline const char *fault_name(ThreadFault f) {
  switch (f) {
    case ThreadFault::NONE: return "none";
    case ThreadFault::STORAGE: return "guard_storage_unavailable";
    case ThreadFault::UART: return "rcp_uart_unavailable";
    case ThreadFault::SILENT_RCP: return "rcp_no_valid_response";
    case ThreadFault::PROTOCOL: return "rcp_spinel_version";
    case ThreadFault::CAPABILITIES: return "rcp_capabilities";
    case ThreadFault::API_VERSION: return "rcp_api_version";
    case ThreadFault::RESET_FAILED: return "rcp_reset_failed";
    case ThreadFault::INCOMPATIBLE: return "rcp_incompatible";
    case ThreadFault::START_TIMEOUT: return "stack_start_timeout";
    case ThreadFault::STACK_ERROR: return "stack_start_error";
    case ThreadFault::HOST_CRASH: return "host_crash_while_thread_armed";
    case ThreadFault::MAINTENANCE: return "maintenance_pause";
  }
  return "unknown";
}
class ThreadGuard {
 public:
  bool restore(ThreadRecord r, bool abnormal_reset) {
    record = r;
    if (!valid_record(record)) { record = {}; quarantine(ThreadFault::STORAGE); return true; }
    if (record.armed && abnormal_reset && !record.quarantined) {
      quarantine(ThreadFault::HOST_CRASH);
      return true;
    }
    // A normal boot begins a new session. Do not attribute a later crash while
    // waiting for Ethernet/preflight to an armed session from an older boot.
    if (record.armed) { record.armed = 0; return true; }
    return false;
  }
  bool arm() {
    if (record.quarantined) return false;
    record.armed = 1;
    return true;
  }
  void quarantine(ThreadFault fault) {
    record.quarantined = 1;
    record.armed = 0;
    record.fault = static_cast<uint32_t>(fault);
    if (fault != ThreadFault::MAINTENANCE && record.faults != UINT32_MAX) ++record.faults;
  }
  void retry() {
    record.quarantined = 0;
    record.armed = 0;
    record.fault = 0;
    if (record.retries != UINT32_MAX) ++record.retries;
  }
  template<typename Persist> bool retry_if_durable(Persist persist) {
    const auto before = record;
    retry();
    if (persist()) return true;
    record = before;
    return false;
  }
  template<typename Persist> bool pause_if_durable(Persist persist) {
    const auto before = record;
    quarantine(ThreadFault::MAINTENANCE);
    if (persist()) return true;
    record = before;
    return false;
  }
  void normal_shutdown() { record.armed = 0; }
  ThreadRecord record{};
};
}  // namespace esphome::low_power_otbr
