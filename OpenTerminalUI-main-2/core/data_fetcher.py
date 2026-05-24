from __future__ import annotations

import sys as _sys

from backend.core import data_fetcher as _module

globals().update(_module.__dict__)
_sys.modules[__name__] = _module
