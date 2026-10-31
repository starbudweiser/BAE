"""Extraction BSA v105 (LZ4, noms incorporés) et BA2 (GNRL compressé, DX10) sur des archives construites ici."""
import os
import struct
import sys
import tempfile
import unittest
import zlib

import lz4.frame

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication  # noqa: E402

import mBAE_MACOS as m  # noqa: E402

APP = QApplication.instance() or QApplication([])


def bsa(flags, body):
    """Un dossier « a », un fichier « b.nif » dont les données sont body."""
    head_len = 36 + 24 + 3 + 16 + 6
    return (
        struct.pack("<4sIIIIIIII", b"BSA\x00", 105, 36, flags, 1, 1, 2, 6, 0)
        + struct.pack("<QIIQ", 1, 1, 0, 0)
        + b"\x02a\x00"
        + struct.pack("<QII", 2, len(body), head_len)
        + b"b.nif\x00"
        + body
    )


def extract(data, suffix):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "x" + suffix)
        with open(path, "wb") as f:
            f.write(data)
        archive = m.BethesdaArchive(path)
        out = os.path.join(d, "out")
        worker, errors = m.ExtractWorker(archive, out), []
        worker.error.connect(errors.append)
        worker.run()
        assert not errors, errors
        return {
            os.path.relpath(os.path.join(p, n), out): open(os.path.join(p, n), "rb").read()
            for p, _, names in os.walk(out) for n in names
        }


class Archives(unittest.TestCase):
    PAYLOAD = b"Gamebryo File Format" * 50

    def test_bsa_v105_lz4(self):
        packed = struct.pack("<I", len(self.PAYLOAD)) + lz4.frame.compress(self.PAYLOAD)
        self.assertEqual(extract(bsa(0x7, packed), ".bsa")["a/b.nif"], self.PAYLOAD)

    def test_bsa_v105_noms_incorpores(self):
        packed = b"\x07a\\b.nif" + struct.pack("<I", len(self.PAYLOAD)) + lz4.frame.compress(self.PAYLOAD)
        self.assertEqual(extract(bsa(0x107, packed), ".bsa")["a/b.nif"], self.PAYLOAD)

    def test_bsa_non_compresse(self):
        self.assertEqual(extract(bsa(0x3, self.PAYLOAD), ".bsa")["a/b.nif"], self.PAYLOAD)

    def test_ba2_gnrl_zlib(self):
        packed = zlib.compress(self.PAYLOAD)
        names = 24 + 36 + len(packed)
        data = (
            struct.pack("<4sI4sIQ", b"BTDX", 1, b"GNRL", 1, names)
            + struct.pack("<IIIIQIII", 1, 2, 3, 0, 60, len(packed), len(self.PAYLOAD), 0xBAADF00D)
            + packed + struct.pack("<H", 5) + b"a/b.c"
        )
        self.assertEqual(extract(data, ".ba2")["a/b.c"], self.PAYLOAD)

    def test_ba2_dx10(self):
        pixels = b"\x11" * 64
        packed = zlib.compress(pixels)
        names = 24 + 48 + len(packed)
        data = (
            struct.pack("<4sI4sIQ", b"BTDX", 1, b"DX10", 1, names)
            + struct.pack("<IIIBBHHHBBBB", 1, 2, 3, 0, 1, 24, 8, 8, 1, 71, 0, 8)
            + struct.pack("<QIIHHI", 72, len(packed), len(pixels), 0, 0, 0xBAADF00D)
            + packed + struct.pack("<H", 5) + b"a/b.d"
        )
        out = extract(data, ".ba2")["a/b.d"]
        self.assertEqual(out[:4], b"DDS ")
        self.assertEqual(struct.unpack("<I", out[128:132])[0], 71)
        self.assertEqual(out[148:], pixels)


if __name__ == "__main__":
    unittest.main()
