"""Read raw or json2 linker-memory reports; never infer missing measurements."""
import json
from pathlib import Path


def read_memory_report(path: Path, *, require_iram: bool = False) -> dict:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("Expected a linker memory report object")
    regions = {}
    if "layout" in data and "memory_types" not in data:
        if data.get("version") != "1.1" or not isinstance(data["layout"], list):
            raise ValueError("Unknown esp-idf-size json2 schema")
        for region in data["layout"]:
            if not isinstance(region, dict) or not isinstance(region.get("name"), str):
                raise ValueError("Malformed linker memory region")
            name = region["name"]
            if name in regions:
                raise ValueError("Duplicate linker memory region: " + name)
            regions[name] = region
        total_key = "total"
    elif "memory_types" in data and "layout" not in data:
        if not isinstance(data["memory_types"], dict):
            raise ValueError("Malformed raw linker memory report")
        regions = data["memory_types"]
        total_key = "size"
    else:
        raise ValueError("Unknown linker memory report schema")

    def require(*names):
        name = next((name for name in names if name in regions), None)
        if name is None:
            raise ValueError("Missing linker memory region: " + "/".join(names))
        region = regions[name]
        if not isinstance(region, dict):
            raise ValueError("Malformed linker memory region: " + name)
        used, total = region.get("used"), region.get(total_key)
        if (type(used) is not int or type(total) is not int
                or total <= 0 or not 0 <= used <= total):
            raise ValueError("Invalid linker memory totals: " + name)
        if total_key == "total" and (type(region.get("free")) is not int
                                     or region["free"] != total - used):
            raise ValueError("Inconsistent linker memory free space: " + name)
        return {"used": used, "size": total}

    result = {"ram": require("DRAM", "DIRAM")}
    if require_iram:
        result["iram"] = require("IRAM")
    return result
