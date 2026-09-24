"""Crew orchestration package.

Keep package import side effects minimal. Individual runtime components are
loaded lazily so importing a leaf module such as mamba2.crew.logger does not
initialize RatesFetcher/ATRManager and create circular imports with indicators.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .atr_manager import ATRManager as ATRManager
    from .rates import RateData as RateData
    from .rates import RatesFetcher as RatesFetcher

__all__ = ["RatesFetcher", "RateData", "ATRManager"]


def __getattr__(name: str):
    if name in {"RatesFetcher", "RateData"}:
        from .rates import RateData, RatesFetcher

        return {"RatesFetcher": RatesFetcher, "RateData": RateData}[name]

    if name == "ATRManager":
        from .atr_manager import ATRManager

        return ATRManager

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
