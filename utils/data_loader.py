import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlencode

import pandas as pd
import requests


logger = logging.getLogger(__name__)

MISSING_MARKERS = ["---", "--", "—", "nan", "NaN", ""]

MONTH_ORDER = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

MONTH_NAME_MAP = {month: index + 1 for index, month in enumerate(MONTH_ORDER)}

REQUIRED_SOURCE_COLUMNS = {
    "Date": "date",
    "Time": "time",
    "Temp_Out": "temperature_c",
    "Out_Hum": "humidity_pct",
    "Wind_Speed": "wind_speed_ms",
    "Bar": "pressure_hpa",
    "Rain": "rain_mm",
}

OPTIONAL_SOURCE_COLUMNS = {
    "UV_Index": "uv_index",
    "Solar_Rad": "solar_rad",
    "Rain_Rate": "rain_rate",
    "Dew_Pt": "dew_point_c",
    "Heat_Index": "heat_index_c",
    "Wind_Chill": "wind_chill_c",
    "Hi_Temp": "high_temperature_c",
    "Low_Temp": "low_temperature_c",
}

METRIC_CONFIG: Dict[str, Dict[str, str]] = {
    "Temperature": {"column": "temperature_c", "unit": "°C", "color": "#2563eb"},
    "Humidity": {"column": "humidity_pct", "unit": "%", "color": "#0f766e"},
    "Pressure": {"column": "pressure_hpa", "unit": "hPa", "color": "#7c3aed"},
    "Wind speed": {"column": "wind_speed_ms", "unit": "m/s", "color": "#db2777"},
    "Rainfall": {"column": "rain_mm", "unit": "mm", "color": "#059669"},
    "UV index": {"column": "uv_index", "unit": "", "color": "#ca8a04"},
    "Solar radiation": {"column": "solar_rad", "unit": " W/m²", "color": "#ea580c"},
}

COMPARISON_METRIC_CONFIG: Dict[str, Dict[str, str]] = {
    "Temperature": {
        "local_column": "temperature_c",
        "met_column": "met_temperature_c",
        "unit": "°C",
        "met_prefixes": "tas, temperature, temp",
    },
    "Rainfall": {
        "local_column": "rain_mm",
        "met_column": "met_rainfall_mm",
        "unit": "mm",
        "met_prefixes": "rain, rainfall, pr",
    },
    "Humidity": {
        "local_column": "humidity_pct",
        "met_column": "met_humidity_pct",
        "unit": "%",
        "met_prefixes": "humidity, hum, hurs",
    },
    "Wind speed": {
        "local_column": "wind_speed_ms",
        "met_column": "met_wind_speed_ms",
        "unit": "m/s",
        "met_prefixes": "wind, sfcwind",
    },
    "Pressure": {
        "local_column": "pressure_hpa",
        "met_column": "met_pressure_hpa",
        "unit": "hPa",
        "met_prefixes": "pressure, pres, psl",
    },
}


class DataValidationError(Exception):
    """Raised when a dashboard dataset is missing required structure or values."""


@dataclass
class WeatherAlert:
    title: str
    message: str
    level: str


@dataclass
class LiveWeather:
    available: bool
    update_time: str = "Unavailable"
    temperature_c: float = float("nan")
    precipitation_mm: float = float("nan")
    wind_speed_ms: float = float("nan")
    humidity_pct: float = float("nan")
    pressure_hpa: float = float("nan")
    error: str = ""
    request_url: str = ""
    status_code: int = 0
    response_preview: str = ""


def normalize_column_name(column: str) -> str:
    return column.strip().replace("  ", " ")


def _to_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def fetch_open_meteo_weather(
    latitude: float = 53.7960,
    longitude: float = -1.7594,
    timeout: int = 10,
) -> LiveWeather:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join(
            [
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation",
                "rain",
                "wind_speed_10m",
                "surface_pressure",
                "pressure_msl",
            ]
        ),
        "wind_speed_unit": "ms",
        "precipitation_unit": "mm",
        "timezone": "Europe/London",
    }
    request_url = f"{url}?{urlencode(params)}"
    response = None

    try:
        response = requests.get(url, params=params, timeout=timeout)
        request_url = response.url
        response_preview = response.text[:500]
        logger.info(
            "Open-Meteo request completed. url=%s status_code=%s response_preview=%r",
            request_url,
            response.status_code,
            response_preview,
        )
        if response.status_code >= 400:
            logger.error(
                "Open-Meteo HTTP error. url=%s status_code=%s response_preview=%r",
                request_url,
                response.status_code,
                response_preview,
            )
        response.raise_for_status()
        payload = response.json()
        current = payload.get("current", {})
    except Exception as exc:
        status_code = response.status_code if response is not None else 0
        response_preview = response.text[:500] if response is not None else ""
        logger.exception(
            "Open-Meteo request failed. url=%s status_code=%s response_preview=%r exception=%s",
            request_url,
            status_code,
            response_preview,
            exc,
        )
        print(
            "Open-Meteo request failed | "
            f"url={request_url} | status_code={status_code} | "
            f"response_preview={response_preview!r} | exception={exc}"
        )
        return LiveWeather(
            available=False,
            error=str(exc),
            request_url=request_url,
            status_code=status_code,
            response_preview=response_preview,
        )

    precipitation = _to_float(current.get("precipitation"))
    rain = _to_float(current.get("rain"))
    if pd.isna(precipitation):
        precipitation = rain
    elif pd.notna(rain):
        precipitation = max(precipitation, rain)

    pressure = _to_float(current.get("surface_pressure"))
    if pd.isna(pressure):
        pressure = _to_float(current.get("pressure_msl"))

    return LiveWeather(
        available=True,
        update_time=str(current.get("time", "Unavailable")),
        temperature_c=_to_float(current.get("temperature_2m")),
        precipitation_mm=precipitation,
        wind_speed_ms=_to_float(current.get("wind_speed_10m")),
        humidity_pct=_to_float(current.get("relative_humidity_2m")),
        pressure_hpa=pressure,
        request_url=request_url,
        status_code=response.status_code,
        response_preview=response.text[:500],
    )


def load_weather_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Weather CSV not found at {path}.")

    try:
        raw_data = pd.read_csv(path)
    except Exception as exc:
        raise DataValidationError(f"Could not read weather CSV: {exc}") from exc

    if raw_data.empty:
        raise DataValidationError("Weather CSV is empty.")

    raw_data.columns = [normalize_column_name(str(column)) for column in raw_data.columns]
    column_lookup = {column.lower(): column for column in raw_data.columns}

    missing = [
        source
        for source in REQUIRED_SOURCE_COLUMNS
        if source.lower() not in column_lookup
    ]
    if missing:
        found = ", ".join(raw_data.columns)
        raise DataValidationError(
            "Missing required weather columns: "
            f"{', '.join(missing)}. Found columns: {found}."
        )

    cleaned = pd.DataFrame()
    for source, target in REQUIRED_SOURCE_COLUMNS.items():
        cleaned[target] = raw_data[column_lookup[source.lower()]]

    for source, target in OPTIONAL_SOURCE_COLUMNS.items():
        if source.lower() in column_lookup:
            cleaned[target] = raw_data[column_lookup[source.lower()]]

    date_values = cleaned["date"].astype(str).str.strip()
    time_values = cleaned["time"].astype(str).str.strip()
    cleaned["datetime"] = pd.to_datetime(
        date_values + " " + time_values,
        dayfirst=True,
        errors="coerce",
    )

    numeric_columns = [
        column for column in cleaned.columns if column not in {"date", "time", "datetime"}
    ]
    for column in numeric_columns:
        cleaned[column] = pd.to_numeric(
            cleaned[column].replace(MISSING_MARKERS, pd.NA),
            errors="coerce",
        )

    invalid_datetime_count = cleaned["datetime"].isna().sum()
    cleaned = cleaned.dropna(subset=["datetime"]).sort_values("datetime")

    if cleaned.empty:
        raise DataValidationError(
            "No valid timestamps could be parsed from the Date and Time columns."
        )

    required_targets = list(REQUIRED_SOURCE_COLUMNS.values())[2:]
    missing_values = [
        column for column in required_targets if cleaned[column].dropna().empty
    ]
    if missing_values:
        raise DataValidationError(
            "Required weather columns contain no valid numeric values: "
            f"{', '.join(missing_values)}."
        )

    cleaned["date"] = cleaned["datetime"].dt.date
    cleaned["month_name"] = cleaned["datetime"].dt.month_name()
    cleaned["month_num"] = cleaned["datetime"].dt.month
    cleaned["year"] = cleaned["datetime"].dt.year
    cleaned["hour"] = cleaned["datetime"].dt.hour
    cleaned["weekday"] = cleaned["datetime"].dt.day_name()
    cleaned["invalid_datetime_rows"] = invalid_datetime_count

    return cleaned.reset_index(drop=True)


def load_met_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    try:
        met_data = pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

    met_data.columns = [str(column).strip().replace("\ufeff", "") for column in met_data.columns]
    monthly_frames = []

    for config in COMPARISON_METRIC_CONFIG.values():
        prefixes = [prefix.strip().lower() for prefix in config["met_prefixes"].split(",")]
        month_columns = [
            column
            for column in met_data.columns
            if any(
                column.lower().startswith(f"{prefix} ")
                or column.lower().startswith(f"{prefix}_")
                or column.lower().startswith(f"{prefix}-")
                for prefix in prefixes
            )
        ]
        if not month_columns:
            continue

        for column in month_columns:
            met_data[column] = pd.to_numeric(met_data[column], errors="coerce")

        monthly = met_data[month_columns].mean().reset_index()
        monthly.columns = ["month_raw", config["met_column"]]
        monthly["month_name"] = monthly["month_raw"].str.split(" ", n=1).str[-1].str.strip()
        monthly["month_num"] = monthly["month_name"].map(MONTH_NAME_MAP)
        monthly = monthly.dropna(subset=["month_num", config["met_column"]])
        monthly["month_num"] = monthly["month_num"].astype(int)
        monthly_frames.append(monthly[["month_num", "month_name", config["met_column"]]])

    if not monthly_frames:
        return pd.DataFrame()

    met_monthly = monthly_frames[0]
    for frame in monthly_frames[1:]:
        met_monthly = pd.merge(met_monthly, frame, on=["month_num", "month_name"], how="outer")

    return met_monthly.sort_values("month_num").reset_index(drop=True)


def get_available_metrics(data: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    return {
        label: config
        for label, config in METRIC_CONFIG.items()
        if config["column"] in data.columns and not data[config["column"]].dropna().empty
    }


def get_correlation_metrics(data: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    return {
        label: config
        for label, config in METRIC_CONFIG.items()
        if config["column"] in data.columns and data[config["column"]].dropna().nunique() > 1
    }


def get_comparison_metric_options(weather_data: pd.DataFrame) -> Dict[str, Dict[str, str]]:
    return {
        label: config
        for label, config in COMPARISON_METRIC_CONFIG.items()
        if config["local_column"] in weather_data.columns
        and not weather_data[config["local_column"]].dropna().empty
    }


def get_comparison_metric_config(metric_label: str) -> Dict[str, str]:
    normalized = metric_label.strip().lower()
    aliases = {
        "temperature": "Temperature",
        "temp": "Temperature",
        "rain": "Rainfall",
        "rainfall": "Rainfall",
        "humidity": "Humidity",
        "wind": "Wind speed",
        "wind speed": "Wind speed",
        "pressure": "Pressure",
    }
    canonical = aliases.get(normalized)
    if canonical is None:
        for label in COMPARISON_METRIC_CONFIG:
            if label.lower() == normalized:
                canonical = label
                break

    if canonical is None or canonical not in COMPARISON_METRIC_CONFIG:
        raise KeyError(f"Unknown comparison metric: {metric_label}")

    return COMPARISON_METRIC_CONFIG[canonical]


def is_temperature_metric(metric_label: str) -> bool:
    normalized = metric_label.strip().lower()
    return normalized in {"temperature", "temp"} or normalized.startswith("temp")


def calculate_correlation_insights(correlation_matrix: pd.DataFrame) -> Tuple[str, str]:
    if correlation_matrix.empty or len(correlation_matrix.columns) < 2:
        return (
            "Not enough metric variety is available for correlation analysis.",
            "Add more numeric weather metrics to unlock stronger comparison insights.",
        )

    pairs = []
    columns = list(correlation_matrix.columns)
    for index, left in enumerate(columns):
        for right in columns[index + 1:]:
            value = correlation_matrix.loc[left, right]
            if pd.notna(value):
                pairs.append((left, right, value))

    if not pairs:
        return (
            "No valid metric pairs were available for correlation analysis.",
            "The selected metrics may contain too many missing values.",
        )

    strongest_positive = max(pairs, key=lambda item: item[2])
    strongest_negative = min(pairs, key=lambda item: item[2])

    positive_text = (
        f"Strongest positive relationship: {strongest_positive[0]} and "
        f"{strongest_positive[1]} with r={strongest_positive[2]:.2f}."
    )
    negative_text = (
        f"Strongest negative relationship: {strongest_negative[0]} and "
        f"{strongest_negative[1]} with r={strongest_negative[2]:.2f}."
    )
    return positive_text, negative_text


def build_live_alerts(live_weather: LiveWeather) -> List[WeatherAlert]:
    if not live_weather.available:
        return []

    alerts: List[WeatherAlert] = []
    temp = live_weather.temperature_c
    rain = live_weather.precipitation_mm
    wind = live_weather.wind_speed_ms
    humidity = live_weather.humidity_pct
    pressure = live_weather.pressure_hpa

    if pd.notna(temp):
        if temp >= 30:
            alerts.append(WeatherAlert("Heat alert", f"Live temperature is {temp:.1f}°C.", "critical"))
        elif temp >= 25:
            alerts.append(WeatherAlert("Hot weather", f"Live temperature is {temp:.1f}°C.", "warning"))
        elif temp <= 0:
            alerts.append(WeatherAlert("Freezing alert", f"Live temperature is {temp:.1f}°C.", "critical"))
        elif temp <= 3:
            alerts.append(WeatherAlert("Cold weather", f"Live temperature is {temp:.1f}°C.", "warning"))

    if pd.notna(rain):
        if rain >= 5:
            alerts.append(WeatherAlert("Heavy rain", f"Live precipitation is {rain:.1f} mm.", "warning"))
        elif rain > 0:
            alerts.append(WeatherAlert("Rain detected", f"Live precipitation is {rain:.1f} mm.", "warning"))

    if pd.notna(wind):
        if wind >= 13.8:
            alerts.append(WeatherAlert("Severe wind", f"Live wind speed is {wind:.1f} m/s.", "critical"))
        elif wind >= 8.3:
            alerts.append(WeatherAlert("Strong wind", f"Live wind speed is {wind:.1f} m/s.", "warning"))

    if pd.notna(humidity) and pd.notna(temp) and humidity >= 85 and temp >= 20:
        alerts.append(
            WeatherAlert(
                "Humid conditions",
                f"Live humidity is {humidity:.0f}% with temperature at {temp:.1f}°C.",
                "warning",
            )
        )

    if pd.notna(pressure):
        if pressure < 980:
            alerts.append(WeatherAlert("Low pressure system", f"Live pressure is {pressure:.0f} hPa.", "warning"))
        elif pressure > 1030:
            alerts.append(WeatherAlert("High pressure system", f"Live pressure is {pressure:.0f} hPa.", "warning"))

    if not alerts:
        alerts.append(
            WeatherAlert(
                "No active live alerts",
                "Open-Meteo live Bradford conditions are within the dashboard alert thresholds.",
                "normal",
            )
        )

    return alerts


def build_monthly_comparison(
    weather_data: pd.DataFrame,
    met_data: pd.DataFrame,
    metric_config: Dict[str, str],
) -> pd.DataFrame:
    if weather_data.empty or met_data.empty:
        return pd.DataFrame()

    local_column = metric_config["local_column"]
    met_column = metric_config["met_column"]
    if local_column not in weather_data.columns or met_column not in met_data.columns:
        return pd.DataFrame()

    local_monthly = (
        weather_data.dropna(subset=[local_column])
        .groupby(["month_num", "month_name"], as_index=False)[local_column]
        .mean()
        .rename(columns={local_column: "local_value"})
    )

    comparison = pd.merge(local_monthly, met_data, on=["month_num", "month_name"], how="inner")
    if comparison.empty:
        return comparison

    comparison = comparison.dropna(subset=["local_value", met_column]).copy()
    if comparison.empty:
        return comparison

    comparison = comparison.rename(columns={met_column: "met_value"})
    comparison["difference"] = comparison["local_value"] - comparison["met_value"]
    comparison["month_name"] = pd.Categorical(
        comparison["month_name"],
        categories=MONTH_ORDER,
        ordered=True,
    )
    return comparison.sort_values("month_num").reset_index(drop=True)
