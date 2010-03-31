from distutils.core import setup 
import sys, os, py2exe
import bc2commander


sys.argv += ['py2exe']

setup(
    name = "BFBC2 Commander",
    version = bc2commander.__version__,
    console = ["bc2commander.py"],
    data_files = ['LICENSE.txt'],
    options = {
        "py2exe": {
            "bundle_files": 2,
        }
    },
) 