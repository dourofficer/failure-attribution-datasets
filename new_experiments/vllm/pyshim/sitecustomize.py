"""Startup shim: directory listings in this environment hide files named libhyper*, so Python's FileFinder cannot
see mpmath/libmp/libhyper.py although the file exists and can be opened. This meta-path finder serves that one
module from its explicit path. Activate with PYTHONPATH=<this dir>."""
import importlib.abc
import importlib.util
import os
import sys

_TARGET = 'mpmath.libmp.libhyper'
_PATH = '/dataDisk/home/thanhdo/.local/lib/python3.10/site-packages/mpmath/libmp/libhyper.py'


class _LibhyperFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == _TARGET and os.path.exists(_PATH):
            return importlib.util.spec_from_file_location(fullname, _PATH)
        return None


sys.meta_path.append(_LibhyperFinder())
