"""crop-water — FAO-56 Penman-Monteith ET0 & solar-pump irrigation scheduler."""

from crop_water.fao56 import (
    CropSoilProfile,
    DailyIrrigationDecision,
    DailyWeather,
    IrrigationScheduleReport,
    penman_monteith_et0,
    schedule_irrigation,
)

__version__ = "0.1.0"

__all__ = [
    "CropSoilProfile",
    "DailyIrrigationDecision",
    "DailyWeather",
    "IrrigationScheduleReport",
    "__version__",
    "penman_monteith_et0",
    "schedule_irrigation",
]
