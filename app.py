from pathlib import Path

import pandas as pd
import streamlit as st

from utils.charts import (
    create_comparison_chart,
    create_correlation_heatmap,
    create_correlation_scatter,
    create_daily_conditions_chart,
    create_metric_chart,
)
from utils.data_loader import (
    DataValidationError,
    LiveWeather,
    build_live_alerts,
    build_monthly_comparison,
    calculate_correlation_insights,
    fetch_open_meteo_weather,
    get_comparison_metric_options,
    get_correlation_metrics,
    get_available_metrics,
    load_met_data,
    load_weather_data,
)
from utils.filters import TIMEFRAME_OPTIONS, filter_by_timeframe


BASE_DIR = Path(__file__).parent
WEATHER_DATA_PATH = BASE_DIR / "data" / "sample_weather_data.csv"
MET_DATA_PATH = BASE_DIR / "data" / "met_data.csv"


st.set_page_config(
    page_title="Bradford Weather Intelligence",
    page_icon=":partly_sunny:",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --page: #f4f7fb;
            --card: #ffffff;
            --ink: #0f172a;
            --heading: #111827;
            --muted: #475569;
            --soft-muted: #64748b;
            --border: #cbd5e1;
            --accent: #2563eb;
            --accent-2: #0f766e;
            --warning: #b45309;
            --danger: #b42318;
        }

        .stApp {
            background: var(--page);
        }

        #MainMenu,
        footer,
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="stDeployButton"],
        .stDeployButton {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            min-height: 0 !important;
        }

        header[data-testid="stHeader"] {
            background: transparent !important;
            height: 0 !important;
            min-height: 0 !important;
            pointer-events: none;
        }

        div[data-testid="stAppViewContainer"] {
            padding-top: 0 !important;
        }

        .main .block-container {
            max-width: 1280px;
            padding-top: 0.35rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3, h4, h5, h6,
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: var(--heading) !important;
            letter-spacing: 0;
        }

        h1 {
            font-size: 2.4rem;
            line-height: 1.05;
            margin-bottom: 0.35rem;
        }

        [data-testid="stMetric"] {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem 1rem 0.85rem;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
            min-height: 128px;
        }

        [data-testid="stMetricLabel"],
        [data-testid="stMetricLabel"] p {
            color: var(--muted) !important;
            font-weight: 700;
        }

        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] div,
        [data-testid="stMetricValue"] span {
            color: var(--ink) !important;
            font-weight: 800;
        }

        [data-testid="stMetricDelta"],
        [data-testid="stMetricDelta"] div,
        [data-testid="stMetricDelta"] svg {
            color: var(--muted) !important;
            fill: var(--muted) !important;
        }

        .stMarkdown,
        .stMarkdown p,
        .stCaption,
        p, span, label {
            color: var(--ink);
        }

        .stCaption,
        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p {
            color: var(--muted) !important;
        }

        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] p {
            color: var(--ink) !important;
            font-weight: 700;
        }

        [data-baseweb="select"] {
            background: #ffffff !important;
        }

        [data-baseweb="select"] > div,
        [data-baseweb="select"] div[role="button"],
        [data-baseweb="select"] div[aria-haspopup="listbox"] {
            background-color: #ffffff !important;
            border-color: var(--border) !important;
            color: var(--ink) !important;
        }

        [data-baseweb="select"] input,
        [data-baseweb="select"] div,
        [data-baseweb="select"] span,
        [data-baseweb="select"] svg {
            color: var(--ink) !important;
            fill: var(--ink) !important;
        }

        [role="listbox"],
        [data-baseweb="menu"] {
            background-color: #ffffff !important;
            color: var(--ink) !important;
        }

        [role="option"],
        [role="option"] div,
        [role="option"] span {
            background-color: #ffffff !important;
            color: var(--ink) !important;
        }

        [role="option"]:hover,
        [role="option"][aria-selected="true"] {
            background-color: #eaf2ff !important;
            color: var(--ink) !important;
        }

        div[data-testid="stAlert"] {
            border-radius: 8px;
            border: 1px solid var(--border);
        }

        div[data-testid="stAlert"] p,
        div[data-testid="stAlert"] span,
        div[data-testid="stAlert"] div {
            color: var(--ink) !important;
            font-weight: 500;
        }

        div[data-testid="stAlert"] strong {
            color: var(--heading) !important;
            font-weight: 800;
        }

        .hero {
            background: linear-gradient(135deg, #ffffff 0%, #edf5ff 100%);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.35rem 1.45rem;
            margin-top: 0;
            margin-bottom: 1rem;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
            color: var(--ink) !important;
        }

        .hero h1 {
            color: var(--heading) !important;
            font-weight: 850;
            text-shadow: none;
        }

        .hero p {
            color: var(--muted) !important;
            font-size: 1.02rem;
            font-weight: 600;
            max-width: 860px;
            margin: 0;
        }

        .hero * {
            color: inherit;
        }

        .badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-top: 1rem;
        }

        .status-badge {
            align-items: center;
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 999px;
            color: var(--ink) !important;
            display: inline-flex;
            font-size: 0.82rem;
            font-weight: 750;
            gap: 0.35rem;
            padding: 0.42rem 0.72rem;
            box-shadow: 0 6px 14px rgba(15, 23, 42, 0.055);
        }

        .status-badge span {
            color: var(--muted) !important;
            font-weight: 700;
        }

        .status-dot {
            border-radius: 999px;
            display: inline-block;
            height: 0.55rem;
            width: 0.55rem;
        }

        .status-dot.online {
            background: #16a34a;
        }

        .status-dot.offline {
            background: #dc2626;
        }

        .nav-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.85rem;
        }

        .nav-pill {
            background: #f8fbff;
            border: 1px solid var(--border);
            border-radius: 999px;
            color: var(--ink) !important;
            font-size: 0.82rem;
            font-weight: 800;
            padding: 0.42rem 0.72rem;
            text-decoration: none !important;
            box-shadow: 0 5px 12px rgba(15, 23, 42, 0.045);
        }

        .nav-pill:hover {
            background: #eaf2ff;
            border-color: #93c5fd;
        }

        .section-label {
            color: #334155;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            margin: 1.25rem 0 0.5rem;
            text-transform: uppercase;
        }

        .status-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            min-height: 126px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.055);
        }

        .status-title {
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 800;
            margin-bottom: 0.35rem;
        }

        .status-value {
            color: var(--ink);
            font-size: 1.75rem;
            font-weight: 780;
            line-height: 1.2;
        }

        .status-note {
            color: var(--soft-muted);
            font-size: 0.78rem;
            font-weight: 600;
            margin-top: 0.25rem;
        }

        .insight-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0 0.2rem;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.055);
        }

        .insight-card strong {
            color: var(--heading);
            font-weight: 850;
        }

        .small-muted {
            color: var(--muted);
            font-size: 0.85rem;
            font-weight: 560;
            line-height: 1.55;
        }

        .controls-label {
            color: #334155;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            margin: 1.05rem 0 -0.2rem;
            text-transform: uppercase;
        }

        div[data-testid="stVerticalBlock"] > div:has(.controls-label) {
            margin-bottom: -0.35rem;
        }

        [data-testid="stPlotlyChart"] {
            background: #ffffff;
            border: 1px solid rgba(203, 213, 225, 0.72);
            border-radius: 8px;
            overflow: hidden;
            padding: 0.25rem;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.045);
        }

        [data-testid="stPlotlyChart"] > div,
        [data-testid="stPlotlyChart"] .js-plotly-plot,
        [data-testid="stPlotlyChart"] .plot-container,
        [data-testid="stPlotlyChart"] .svg-container,
        [data-testid="stPlotlyChart"] svg {
            border-radius: 8px !important;
            overflow: hidden !important;
        }

        [data-testid="stPlotlyChart"] .main-svg {
            border-radius: 8px !important;
        }

        @media (max-width: 900px) {
            .main .block-container {
                padding: 0.35rem 0.75rem 2rem;
            }

            h1 {
                font-size: 1.95rem;
                line-height: 1.12;
            }

            .hero {
                padding: 1rem;
                margin-bottom: 0.75rem;
            }

            .hero p {
                font-size: 0.95rem;
            }

            div[data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }

            .status-card,
            [data-testid="stMetric"],
            .insight-card {
                min-height: auto;
                margin-bottom: 0.55rem;
            }

            .status-value {
                font-size: 1.45rem;
            }

            .section-label,
            .controls-label {
                margin-top: 0.95rem;
            }

            [data-testid="stPlotlyChart"] {
                padding: 0;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_number(value: float, unit: str = "", decimals: int = 1) -> str:
    if pd.isna(value):
        return "No data"
    return f"{value:.{decimals}f}{unit}"


@st.cache_data(ttl=300, show_spinner=False)
def load_live_weather() -> LiveWeather:
    return fetch_open_meteo_weather()


def render_header(live_weather: LiveWeather, latest_station_timestamp: pd.Timestamp) -> None:
    live_status = "Online" if live_weather.available else "Offline"
    live_dot = "online" if live_weather.available else "offline"
    live_update = live_weather.update_time if live_weather.available else "Unavailable"
    station_timestamp = latest_station_timestamp.strftime("%d %b %Y, %H:%M")

    st.markdown(
        f"""
        <div class="hero">
            <h1>Bradford Weather Intelligence</h1>
            <p>
                Interactive portfolio dashboard for live weather alerts, historical station analysis,
                data cleaning, MET comparison analytics, and responsive visual exploration of
                University of Bradford roof-station readings.
            </p>
            <div class="badge-row">
                <div class="status-badge">
                    <i class="status-dot {live_dot}"></i>
                    Open-Meteo Live: <span>{live_status}</span>
                </div>
                <div class="status-badge">
                    Station Dataset: <span>Historical CSV</span>
                </div>
                <div class="status-badge">
                    Latest live update: <span>{live_update}</span>
                </div>
                <div class="status-badge">
                    Latest station timestamp: <span>{station_timestamp}</span>
                </div>
            </div>
            <div class="nav-row">
                <a class="nav-pill" href="#overview">Overview</a>
                <a class="nav-pill" href="#trends">Trends</a>
                <a class="nav-pill" href="#correlations">Correlations</a>
                <a class="nav-pill" href="#met-comparison">MET Comparison</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_live_cards(live_weather: LiveWeather) -> None:
    timestamp = live_weather.update_time if live_weather.available else "Unavailable"
    readings = [
        ("Temperature", live_weather.temperature_c, "°C", "Open-Meteo live feed"),
        ("Humidity", live_weather.humidity_pct, "%", "Open-Meteo live feed"),
        ("Wind", live_weather.wind_speed_ms, " m/s", "Open-Meteo live feed"),
        ("Pressure", live_weather.pressure_hpa, " hPa", "Open-Meteo live feed"),
        ("Rain", live_weather.precipitation_mm, " mm", "Open-Meteo live feed"),
    ]

    st.markdown('<a id="overview"></a>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Live Bradford Weather Summary</div>', unsafe_allow_html=True)
    if not live_weather.available:
        st.info("Open-Meteo live feed unavailable — live weather summary cannot be refreshed right now.")
        render_open_meteo_error(live_weather)

    cols = st.columns(5)
    for col, (title, value, unit, note) in zip(cols, readings):
        with col:
            st.markdown(
                f"""
                <div class="status-card">
                    <div class="status-title">{title}</div>
                    <div class="status-value">{format_number(value, unit)}</div>
                    <div class="status-note">{note}<br>{timestamp}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_open_meteo_error(live_weather: LiveWeather) -> None:
    if live_weather.available:
        return

    status = live_weather.status_code if live_weather.status_code else "No HTTP response"
    with st.expander("Open-Meteo API status / error details", expanded=False):
        st.markdown(f"**Request URL:** `{live_weather.request_url or 'Unavailable'}`")
        st.markdown(f"**HTTP status code:** `{status}`")
        st.markdown(f"**Exception:** `{live_weather.error or 'Unavailable'}`")
        if live_weather.response_preview:
            st.code(live_weather.response_preview, language="text")
        else:
            st.caption("No response body was returned.")


def render_station_latest_reading(latest: pd.Series) -> None:
    readings = [
        ("Temperature", latest.get("temperature_c"), "°C"),
        ("Humidity", latest.get("humidity_pct"), "%"),
        ("Wind", latest.get("wind_speed_ms"), " m/s"),
        ("Pressure", latest.get("pressure_hpa"), " hPa"),
        ("Rain", latest.get("rain_mm"), " mm"),
    ]

    timestamp = latest["datetime"].strftime("%d %b %Y, %H:%M")
    st.markdown(
        '<div class="section-label">Latest Available Station Dataset Reading</div>',
        unsafe_allow_html=True,
    )
    st.caption(f"Source: historical station CSV. Latest timestamp: {timestamp}.")
    cols = st.columns(5)
    for col, (title, value, unit) in zip(cols, readings):
        with col:
            st.metric(title, format_number(value, unit))


def render_period_metrics(data: pd.DataFrame) -> None:
    st.markdown(
        '<div class="section-label">Selected Historical Period Performance</div>',
        unsafe_allow_html=True,
    )
    cards = [
        ("Avg temperature", data["temperature_c"].mean(), "°C"),
        ("Peak temperature", data["temperature_c"].max(), "°C"),
        ("Avg humidity", data["humidity_pct"].mean(), "%"),
        ("Max wind", data["wind_speed_ms"].max(), " m/s"),
        ("Total rain", data["rain_mm"].sum(), " mm"),
    ]
    cols = st.columns(5)
    for col, (label, value, unit) in zip(cols, cards):
        with col:
            st.metric(label, format_number(value, unit))


def render_live_alerts(live_weather: LiveWeather) -> None:
    st.markdown('<div class="section-label">Live Weather Alerts</div>', unsafe_allow_html=True)
    st.caption("Source: Open-Meteo live Bradford weather")

    if not live_weather.available:
        st.info("Live alerts unavailable — showing historical dataset only.")
        render_open_meteo_error(live_weather)
        return

    for alert in build_live_alerts(live_weather):
        message = f"**{alert.title}**  \n{alert.message}"
        if alert.level == "normal":
            st.success(message)
        elif alert.level == "warning":
            st.warning(message)
        else:
            st.error(message)


def render_dataset_health(data: pd.DataFrame, met_data: pd.DataFrame) -> None:
    start = data["datetime"].min().strftime("%d %b %Y")
    end = data["datetime"].max().strftime("%d %b %Y")
    met_status = "Available" if not met_data.empty else "Not available"
    st.markdown(
        f"""
        <div class="insight-card">
            <strong>Dataset health</strong><br>
            <span class="small-muted">
                {len(data):,} cleaned readings from {start} to {end}. MET comparison data: {met_status}.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_correlation_analysis(data: pd.DataFrame) -> None:
    st.markdown(
        '<div class="section-label">Historical Metric Correlation Analysis</div>',
        unsafe_allow_html=True,
    )
    st.caption("Source: historical University of Bradford station CSV.")
    correlation_metrics = get_correlation_metrics(data)
    if len(correlation_metrics) < 2:
        st.info("At least two numeric weather metrics are needed for correlation analysis.")
        return

    metric_frame = pd.DataFrame(
        {
            label: data[config["column"]]
            for label, config in correlation_metrics.items()
        }
    ).dropna(how="all")
    correlation_matrix = metric_frame.corr(numeric_only=True)
    positive_text, negative_text = calculate_correlation_insights(correlation_matrix)

    heatmap_col, insight_col = st.columns([2, 1])
    with heatmap_col:
        st.plotly_chart(create_correlation_heatmap(correlation_matrix), width="stretch")
    with insight_col:
        st.markdown(
            f"""
            <div class="insight-card">
                <strong>Correlation insight</strong><br>
                <span class="small-muted">
                    {positive_text}<br><br>
                    {negative_text}<br><br>
                    Correlation values range from -1 to +1 and describe how strongly
                    two metrics move together in the cleaned station dataset.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    labels = list(correlation_metrics.keys())
    scatter_cols = st.columns([1, 1, 3])
    with scatter_cols[0]:
        x_label = st.selectbox("Correlation X metric", labels, index=0)
    with scatter_cols[1]:
        default_y_index = 1 if len(labels) > 1 else 0
        y_label = st.selectbox("Correlation Y metric", labels, index=default_y_index)

    if x_label == y_label:
        st.info("Choose two different metrics to see a pairwise scatter comparison.")
    else:
        st.plotly_chart(
            create_correlation_scatter(
                data,
                x_label,
                correlation_metrics[x_label]["column"],
                y_label,
                correlation_metrics[y_label]["column"],
            ),
            width="stretch",
        )


def main() -> None:
    inject_styles()

    with st.spinner("Loading and cleaning weather datasets..."):
        try:
            weather_data = load_weather_data(WEATHER_DATA_PATH)
            met_data = load_met_data(MET_DATA_PATH)
        except (FileNotFoundError, DataValidationError) as exc:
            st.error(str(exc))
            st.info(
                "Check that `data/sample_weather_data.csv` exists and contains Date, Time, "
                "temperature, humidity, pressure, wind, and rain columns."
            )
            st.stop()

    live_weather = load_live_weather()
    metrics = get_available_metrics(weather_data)
    latest = weather_data.iloc[-1]

    render_header(live_weather, latest["datetime"])

    render_live_cards(live_weather)

    render_station_latest_reading(latest)

    render_dataset_health(weather_data, met_data)

    st.markdown('<a id="trends"></a>', unsafe_allow_html=True)
    st.markdown('<div class="controls-label">Explore Historical Station Dataset</div>', unsafe_allow_html=True)
    control_cols = st.columns([1, 1, 3])
    with control_cols[0]:
        selected_metric_label = st.selectbox("Metric", list(metrics.keys()))
    with control_cols[1]:
        selected_timeframe = st.selectbox("Timeframe", TIMEFRAME_OPTIONS)

    filtered_data = filter_by_timeframe(weather_data, selected_timeframe)
    selected_metric = metrics[selected_metric_label]

    render_period_metrics(filtered_data)

    graph_col, side_col = st.columns([2.15, 1])
    with graph_col:
        st.plotly_chart(
            create_metric_chart(filtered_data, selected_metric),
            width="stretch",
        )
    with side_col:
        render_live_alerts(live_weather)
        st.caption(
            f"{len(filtered_data):,} historical station readings shown for "
            f"{selected_timeframe.lower()}, anchored to the latest CSV timestamp."
        )

    st.markdown('<div class="section-label">Historical Daily Conditions Overview</div>', unsafe_allow_html=True)
    st.caption("Source: historical University of Bradford station CSV.")
    st.plotly_chart(create_daily_conditions_chart(filtered_data), width="stretch")

    st.markdown('<a id="correlations"></a>', unsafe_allow_html=True)
    render_correlation_analysis(filtered_data)

    st.markdown('<a id="met-comparison"></a>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Bradford MET comparison</div>', unsafe_allow_html=True)
    st.caption("Source: historical station CSV compared with available Bradford MET monthly baseline data.")
    comparison_metrics = get_comparison_metric_options(weather_data)
    selected_comparison_metric = st.selectbox(
        "Comparison metric",
        list(comparison_metrics.keys()),
        index=0,
    )
    comparison_config = comparison_metrics[selected_comparison_metric]
    comparison = build_monthly_comparison(weather_data, met_data, comparison_config)
    if comparison.empty:
        st.info(
            f"Bradford MET comparison data is not available for {selected_comparison_metric.lower()} "
            "in the current MET file. This dataset currently provides matched monthly temperature "
            "baseline values, so choose Temperature to compare against the local station readings."
        )
    else:
        met_cols = st.columns([2, 1])
        with met_cols[0]:
            st.plotly_chart(
                create_comparison_chart(
                    comparison,
                    selected_comparison_metric,
                    comparison_config["unit"],
                ),
                width="stretch",
            )
        with met_cols[1]:
            latest_month = comparison.iloc[-1]
            st.markdown(
                f"""
                <div class="insight-card">
                    <strong>Comparison insight</strong><br>
                    <span class="small-muted">
                        Latest matched month: {latest_month["month_name"]}.<br>
                        Local average: {latest_month["local_value"]:.1f}{comparison_config["unit"]}.<br>
                        MET baseline: {latest_month["met_value"]:.1f}{comparison_config["unit"]}.<br>
                        Difference: {latest_month["difference"]:+.1f}{comparison_config["unit"]}.
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
