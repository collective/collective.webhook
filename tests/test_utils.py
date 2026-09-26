# -*- coding: utf-8 -*-
from collective.webhook.utils import create_tarball
from io import BytesIO

import os
import tarfile
import tempfile
import unittest


class CreateTarballTests(unittest.TestCase):
    def test_nested_directories(self):
        with tempfile.TemporaryDirectory() as path:
            os.makedirs(os.path.join(path, "sub", "deeper"))
            for name, data in (
                ("top.txt", b"top"),
                (os.path.join("sub", "mid.txt"), b"mid"),
                (os.path.join("sub", "deeper", "low.txt"), b"low"),
            ):
                with open(os.path.join(path, name), "wb") as fp:
                    fp.write(data)
            archive = create_tarball(path)

        with tarfile.open(fileobj=BytesIO(archive), mode="r:gz") as tar:
            files = {
                m.name: tar.extractfile(m).read()
                for m in tar.getmembers()
                if m.isfile()
            }
            dirs = {m.name for m in tar.getmembers() if m.isdir()}
        self.assertEqual({"sub", "sub/deeper"}, dirs)
        self.assertEqual(
            {"top.txt": b"top", "sub/mid.txt": b"mid", "sub/deeper/low.txt": b"low"},
            files,
        )
