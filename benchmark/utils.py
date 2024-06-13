# © Crown-owned copyright 2024, Defence Science and Technology Laboratory UK
import platform
from typing import Dict

import psutil
from GPUtil import GPUtil


def get_size(size_bytes: int) -> str:
    """
    Scale bytes to its proper format.

    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'

    :
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if size_bytes < factor:
            return f"{size_bytes:.2f}{unit}B"
        size_bytes /= factor


def _get_system_info() -> Dict:
    """Builds and returns a dict containing system info."""
    uname = platform.uname()
    cpu_freq = psutil.cpu_freq()
    virtual_mem = psutil.virtual_memory()
    swap_mem = psutil.swap_memory()
    gpus = GPUtil.getGPUs()
    return {
        "System": {
            "OS": uname.system,
            "OS Version": uname.version,
            "Machine": uname.machine,
            "Processor": uname.processor,
        },
        "CPU": {
            "Physical Cores": psutil.cpu_count(logical=False),
            "Total Cores": psutil.cpu_count(logical=True),
            "Max Frequency": f"{cpu_freq.max:.2f}Mhz",
        },
        "Memory": {"Total": get_size(virtual_mem.total), "Swap Total": get_size(swap_mem.total)},
        "GPU": [{"Name": gpu.name, "Total Memory": f"{gpu.memoryTotal}MB"} for gpu in gpus],
    }
