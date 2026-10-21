"""DFR0627 address decoding, independent of ESPHome schema machinery.

DFRobot reserves low address bits for channel/FIFO selection. Its reference
documents ACKs throughout the matching eight-address block, including unused
channel encodings. Disabling UART2 does not release those I2C addresses.
https://wiki.dfrobot.com/dfr0627/docs/20907
"""

UART1_REGISTER_ADDRESSES = (0x10, 0x30, 0x50, 0x70)


def validate_address_plan(config, full_config):
    address = config["address"]
    if address not in UART1_REGISTER_ADDRESSES:
        raise ValueError("DFR0627 UART1 register address must be 0x10, 0x30, 0x50 or 0x70 to match IA1/IA0")
    bus = str(config["i2c_id"])
    owner = str(config["id"])

    def visit(node):
        if isinstance(node, dict):
            if "address" in node and "i2c_id" in node and str(node.get("id")) != owner:
                other = node["address"]
                if str(node["i2c_id"]) == bus and address <= other <= address + 7:
                    raise ValueError(
                        f"DFR0627 reserves 0x{address:02X}–0x{address + 7:02X} on {bus}; "
                        f"device {node.get('id', 'unnamed')} at 0x{other:02X} overlaps. "
                        "For BME680 at 0x76/0x77 set IA1=1, IA0=0 and DFR0627 address=0x50."
                    )
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(full_config)
