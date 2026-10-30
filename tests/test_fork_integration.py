import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from FlashGBX import app
from FlashGBX.FlashGBX import LoadConfig
from FlashGBX.hw_Chromatic import GbxDevice


class ForkIntegrationTests(unittest.TestCase):
    def test_chromatic_implements_52_device_interface(self):
        self.assertFalse(GbxDevice.__abstractmethods__)
        with patch.object(GbxDevice, "_load_lk"):
            device = GbxDevice()
        self.assertEqual(device.GetSupportedModes(), ["DMG"])
        self.assertTrue(device.SupportsAudioAsWe())
        self.assertIn("hw_Chromatic", app.HW_DEVICE_MODULES)
        self.assertTrue(any(module.__name__.endswith(".hw_Chromatic") for module in app.HW_DEVICES))

    def test_missing_profiles_are_added_without_overwriting_custom_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "res").mkdir()
            config_path = root / "config"
            config_path.mkdir()
            custom = {"type": "DMG", "names": ["custom"]}
            existing = config_path / "fc_DMG_existing.txt"
            existing.write_text(json.dumps(custom), encoding="utf-8")
            with zipfile.ZipFile(root / "res" / "config.zip", "w") as archive:
                archive.writestr(existing.name, json.dumps({"type": "DMG", "names": ["replacement"]}))
                archive.writestr("fc_DMG_new.txt", json.dumps({"type": "DMG", "names": ["new"]}))
            with patch("FlashGBX.FlashGBX.ReadConfigFiles", return_value=(app.AppInfo.VERSION, [str(existing)])):
                loaded = LoadConfig({"app_path": str(root), "config_path": str(config_path)})
            self.assertEqual(set(loaded["flashcarts"]["DMG"]), {"custom", "new"})
            self.assertEqual(json.loads(existing.read_text()), custom)


if __name__ == "__main__":
    unittest.main()
