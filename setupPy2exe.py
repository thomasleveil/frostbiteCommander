from distutils.core import setup 
import sys, os, py2exe
import frostbiteCommander


sys.argv += ['py2exe']

setup(
    name = "Frostbite Commander",
    version = frostbiteCommander.__version__,
    console = ["frostbiteCommander.py"],
    data_files = ['LICENSE.txt'],
    options = {
        "py2exe": {
            "bundle_files": 2,
        }
    },
) 