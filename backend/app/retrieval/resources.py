"""Local physical-memory readiness checks; no model loading or dependencies."""

import ctypes
import os
import sys

RAM_RESERVE_BYTES = 1536 * 1024**2


def available_ram_bytes() -> int:
    """Read available physical RAM; fail closed on unsupported platforms."""
    if sys.platform == "win32":
        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
                *[(name, ctypes.c_ulonglong) for name in (
                    "total", "available", "page_total", "page_available",
                    "virtual_total", "virtual_available", "extended",
                )],
            ]

        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            raise RuntimeError("Physical RAM check failed")
        return status.available
    if sys.platform.startswith("linux"):
        with open("/proc/meminfo", encoding="ascii") as source:
            for line in source:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) * 1024
        raise RuntimeError("Physical RAM check unavailable")
    if sys.platform == "darwin":
        # Free pages alone are conservative; do not assume reclaimable memory.
        return os.sysconf("SC_AVPHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
    raise RuntimeError("Physical RAM check unavailable")
