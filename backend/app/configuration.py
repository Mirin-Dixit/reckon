"""Reckon settings with explicit legacy environment compatibility."""

import os
from collections.abc import Mapping


def environment(values: Mapping[str, str] | None = None) -> dict[str, str]:
    """Prefer RECKON_*; retain RAGBENCH_* as fallback without mutating os.environ."""
    result = dict(os.environ if values is None else values)
    for key, value in tuple(result.items()):
        if key.startswith("RAGBENCH_"):
            result.setdefault("RECKON_" + key[len("RAGBENCH_"):], value)
    return result
