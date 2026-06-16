import sys
import os
import importlib.util
import types

# Exclude backbone-python's own __init__.py from pytest collection
collect_ignore = ["__init__.py"]

_here = os.path.dirname(os.path.abspath(__file__))

if "backbone" not in sys.modules:
    mod = types.ModuleType("backbone")
    mod.__file__ = os.path.join(_here, "__init__.py")
    mod.__path__ = [_here]
    mod.__package__ = "backbone"
    sys.modules["backbone"] = mod

    spec = importlib.util.spec_from_file_location(
        "backbone",
        os.path.join(_here, "__init__.py"),
        submodule_search_locations=[_here],
    )
    spec.loader.exec_module(mod)
