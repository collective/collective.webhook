# -*- coding: utf-8 -*-
# noinspection PyPep8Naming
from io import BytesIO

import os
import tarfile


def populate_tarball(tar, path, prefix=''):
    for name in os.listdir(path):
        if os.path.isdir(os.path.join(path, name)):

            # Create sub-directory
            info = tarfile.TarInfo(prefix + name)
            info.type = tarfile.DIRTYPE
            tar.addfile(info, BytesIO())

            # Populate sub-directory
            populate_tarball(tar, path[name], prefix + name + '/')

        else:
            # Add file
            with open(os.path.join(path, name), 'rb') as fp:
                data = fp.read()
            info = tarfile.TarInfo(prefix + name)
            info.size = len(data)
            tar.addfile(info, BytesIO(data))


# noinspection PyPep8Naming
def create_tarball(path):
    fb = BytesIO()
    tar = tarfile.open(fileobj=fb, mode='w:gz')

    # Recursively populate tarball
    populate_tarball(tar, path)

    tar.close()
    return fb.getvalue()
