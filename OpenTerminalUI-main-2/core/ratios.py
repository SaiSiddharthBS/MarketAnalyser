from __future__ import annotations

import sys as _sys

from backend.core import ratios as _module

globals().update(_module.__dict__)
_sys.modules[__name__] = _module
