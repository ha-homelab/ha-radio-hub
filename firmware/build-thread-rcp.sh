#!/usr/bin/env bash
# Build only. No erase, DFU, serial access, or network commissioning.
set -euo pipefail
RCP_REVISION=1ff0a4905e436eb79605582f36b689063b1282ef
RCP_BUILD_DIR=${1:-"$PWD/.build/thread-rcp"}
if [ -e "$RCP_BUILD_DIR" ]; then
  echo "Refusing to replace existing build directory: $RCP_BUILD_DIR" >&2
  exit 1
fi
command -v arm-none-eabi-gcc >/dev/null || {
  echo "Install an Arm GNU bare-metal toolchain (arm-none-eabi-gcc) and CMake/Ninja first." >&2
  exit 1
}
git clone https://github.com/openthread/ot-nrf528xx.git "$RCP_BUILD_DIR"
git -C "$RCP_BUILD_DIR" checkout --detach "$RCP_REVISION"
git -C "$RCP_BUILD_DIR" submodule update --init --recursive
cd "$RCP_BUILD_DIR"
./script/build nrf52840 USB_trans -DOT_BOOTLOADER=USB -DOT_RCP=ON
arm-none-eabi-objcopy -O ihex build/bin/ot-rcp ot-rcp-pca10059.hex
echo "Built $RCP_BUILD_DIR/ot-rcp-pca10059.hex. Flash with Nordic Programmer; preserve bootloader."
