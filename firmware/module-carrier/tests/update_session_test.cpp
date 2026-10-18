#include "update_session.h"
#include <cassert>
#include <string>
using namespace esphome::low_power_otbr;
int main(int argc, char **argv) {
  assert(argc == 2);
  const std::string test = argv[1];
  if (test == "token_validation") {
    assert(valid_update_token("0123456789abcdef0123456789abcdef"));
    for (const std::string bad : {"", "abc", "0123456789ABCDEF0123456789ABCDEF", "0123456789abcdef0123456789abcdeg", "0123456789abcdef0123456789abcdef\n"})
      assert(!valid_update_token(bad));
  } else if (test == "token_comparison") {
    std::string expected(32, 'a'), got = expected;
    assert(equal_update_token(expected.data(), got.data()));
    for (size_t i = 0; i < 32; ++i) {
      got = expected; got[i] = 'b'; assert(!equal_update_token(expected.data(), got.data()));
    }
  } else if (test == "maintenance_interlock") {
    assert(update_may_arm(true, true, false, true, 0));
    assert(!update_may_arm(false, true, false, true, 0));
    assert(!update_may_arm(true, false, false, true, 0));
    assert(!update_may_arm(true, true, true, true, 0));
    assert(!update_may_arm(true, true, false, false, 0));
    assert(!update_may_arm(true, true, false, true, 1));
    assert(!update_may_arm(true, true, false, true, 2));
  } else if (test == "deadline_wrap") {
    assert(update_window_open(0x00000010, 0xfffffff0, 33));
    assert(!update_window_open(0x00000010, 0xfffffff0, 32));
    assert(update_window_open(59999, 0, 60000));
    assert(!update_window_open(60000, 0, 60000));
    assert(!update_window_open(600000, 0, 600000));
  } else return 2;
}
