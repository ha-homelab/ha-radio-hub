"""Keep intended source and image pins consistent with repository inputs."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

class VersionMetadataTests(unittest.TestCase):
    def test_metadata_matches_intended_firmware_and_image_inputs(self):
        metadata = json.loads((ROOT / "software/versions.json").read_text())
        firmware = (ROOT / "firmware/requirements.txt").read_text().strip()
        self.assertEqual(firmware, "esphome==" + metadata["esphome"])
        compose = (ROOT / "software/compose.yaml").read_text()
        self.assertEqual(re.search(r"image: (openthread/border-router@sha256:[0-9a-f]+)", compose)[1], metadata["otbr_image"])
        self.assertIn("source " + metadata["otbr_source"] + ".", compose)
        dockerfile = (ROOT / "software/ser2net/Dockerfile").read_text()
        self.assertEqual(re.search(r"^FROM (.+)$", dockerfile, re.M)[1], metadata["ser2net_base"])
        self.assertIn("ser2net=" + metadata["ser2net_debian_package"], dockerfile)

if __name__ == "__main__":
    unittest.main()
