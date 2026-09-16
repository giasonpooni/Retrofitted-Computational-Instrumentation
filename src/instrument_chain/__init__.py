"""Measurement-chain contract for retrofitted computational instruments."""

from .calibration import apply_calibration
from .manifest import SCHEMA, Assembly, load_assembly
from .observation import Observation, Quality, acquire_or_unavailable
from .receiver import receive, replay
from .transport import Delivery, deliver

__all__ = [
    "SCHEMA",
    "Assembly",
    "Delivery",
    "Observation",
    "Quality",
    "acquire_or_unavailable",
    "apply_calibration",
    "deliver",
    "load_assembly",
    "receive",
    "replay",
]

__version__ = "0.1.0"
