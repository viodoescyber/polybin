import unittest
import os
import shutil
import tempfile
from polybin import build

ASSETS = "tests/assets"
ICON = os.path.join(ASSETS, "sample.ico")
MP4 = os.path.join(ASSETS, "sample.mp4")
ZIP = os.path.join(ASSETS, "sample.pptx")

class TestPolyglot(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = os.path.join(self.temp_dir, "polyglot.out")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _assert_contains_signatures(self, data: bytes, signatures: list):
        for sig in signatures:
            self.assertIn(sig, data)

    def test_ico_and_mp4(self):
        build(self.output_path, ico_path=ICON, mp4_path=MP4)
        with open(self.output_path, 'rb') as f:
            data = f.read()
        self._assert_contains_signatures(data, [
            b'\x00\x00\x01\x00',  # ICO header
            b'ftyp'               # MP4
        ])

    def test_ico_and_zip(self):
        build(self.output_path, ico_path=ICON, zip_paths=[ZIP])
        with open(self.output_path, 'rb') as f:
            data = f.read()
        self._assert_contains_signatures(data, [
            b'\x00\x00\x01\x00',  # ICO header
            b'PK\x05\x06'         # End of central directory
        ])

    def test_mp4_and_zip(self):
        build(self.output_path, mp4_path=MP4, zip_paths=[ZIP])
        with open(self.output_path, 'rb') as f:
            data = f.read()
        self._assert_contains_signatures(data, [
            b'ftyp',           # MP4 header
            b'PK\x05\x06'      # End of central directory
        ])

    def test_all(self):
        build(self.output_path, ico_path=ICON, mp4_path=MP4, zip_paths=[ZIP])
        with open(self.output_path, 'rb') as f:
            data = f.read()
        self._assert_contains_signatures(data, [
            b'\x00\x00\x01\x00',  # ICO header
            b'ftyp',              # MP4 header
            b'PK\x05\x06'         # End of central directory
        ])

    def test_missing_input(self):
        with self.assertRaises(FileNotFoundError):
            build(self.output_path, ico_path="nonexistent.ico", mp4_path=MP4)

    def test_too_few_inputs(self):
        with self.assertRaises(ValueError):
            build(self.output_path, ico_path=ICON) 

if __name__ == "__main__":
    unittest.main()
