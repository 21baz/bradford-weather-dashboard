from typing import List

import pandas as pd


TIMEFRAME_OPTIONS: List[str] = ["Last 7 days", "Last month", "Last year", "All time"]

TIMEFRAME_DURATIONS = {
    "Last 7 days": pd.Timedelta(days=7),
    "Last month": pd.Timedelta(days=30),
    "Last year": pd.Timedelta(days=365),
    "All time": None,
}


def filter_by_timeframe(data: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    if timeframe not in TIMEFRAME_DURATIONS:
        raise ValueError(f"Unknown timeframe: {timeframe}")

    duration = TIMEFRAME_DURATIONS[timeframe]
    if duration is None:
        return data.copy()

    latest_timestamp = data["datetime"].max()
    start_timestamp = latest_timestamp - duration
    filtered = data[data["datetime"] >= start_timestamp].copy()

    if filtered.empty:
        return data.tail(1).copy()

    return filtered
