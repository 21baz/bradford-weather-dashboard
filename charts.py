from typing import Dict

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


CHART_TEMPLATE = "plotly_white"
TEXT_COLOR = "#0f172a"
SECONDARY_TEXT_COLOR = "#334155"
GRID_COLOR = "#dbe4ef"
BORDER_COLOR = "#cbd5e1"


def apply_dashboard_layout(fig: go.Figure, height: int = 460) -> go.Figure:
    fig.update_layout(
        template=CHART_TEMPLATE,
        height=height,
        margin=dict(l=18, r=18, t=58, b=24),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=SECONDARY_TEXT_COLOR, size=13),
        ),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(
            family="Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
            color=TEXT_COLOR,
            size=13,
        ),
        title=dict(
            font=dict(color=TEXT_COLOR, size=20),
            x=0.01,
            xanchor="left",
        ),
        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor=BORDER_COLOR,
            font=dict(color=TEXT_COLOR, size=13),
        ),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor=GRID_COLOR,
        zerolinecolor=BORDER_COLOR,
        linecolor=BORDER_COLOR,
        tickfont=dict(color=SECONDARY_TEXT_COLOR, size=12),
        title_font=dict(color=TEXT_COLOR, size=13),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=GRID_COLOR,
        zerolinecolor=BORDER_COLOR,
        linecolor=BORDER_COLOR,
        tickfont=dict(color=SECONDARY_TEXT_COLOR, size=12),
        title_font=dict(color=TEXT_COLOR, size=13),
    )
    return fig


def create_metric_chart(data: pd.DataFrame, metric: Dict[str, str]) -> go.Figure:
    column = metric["column"]
    unit = metric["unit"]
    chart_data = data[["datetime", column]].dropna()
    show_markers = len(chart_data) <= 1500

    fig = px.line(
        chart_data,
        x="datetime",
        y=column,
        markers=show_markers,
        title=f"{column.replace('_', ' ').title()} trend",
        labels={"datetime": "Date", column: f"{column.replace('_', ' ').title()} ({unit})"},
    )
    fig.update_traces(
        line=dict(color=metric["color"], width=2.8),
        marker=dict(color=metric["color"], size=5),
        hovertemplate="%{x|%d %b %Y %H:%M}<br>%{y:.2f} " + unit,
    )

    if len(chart_data) >= 8:
        rolling = chart_data.set_index("datetime")[column].rolling(8, min_periods=1).mean()
        fig.add_trace(
            go.Scatter(
                x=rolling.index,
                y=rolling.values,
                mode="lines",
                name="Rolling average",
                line=dict(color="#111827", width=2, dash="dot"),
                hovertemplate="%{x|%d %b %Y %H:%M}<br>%{y:.2f} " + unit,
            )
        )

    return apply_dashboard_layout(fig, height=500)


def create_daily_conditions_chart(data: pd.DataFrame) -> go.Figure:
    daily = (
        data.set_index("datetime")[["temperature_c", "rain_mm", "wind_speed_ms"]]
        .resample("D")
        .agg(
            temperature_min_c=("temperature_c", "min"),
            temperature_max_c=("temperature_c", "max"),
            rainfall_mm=("rain_mm", "sum"),
            average_wind_ms=("wind_speed_ms", "mean"),
        )
        .dropna(how="all")
        .reset_index()
    )

    fig = go.Figure()
    fig.add_bar(
        x=daily["datetime"],
        y=daily["rainfall_mm"],
        name="Daily rainfall",
        marker_color="#60a5fa",
        opacity=0.45,
        hovertemplate="%{x|%d %b %Y}<br>%{y:.2f} mm",
    )
    fig.add_trace(
        go.Scatter(
            x=daily["datetime"],
            y=daily["temperature_min_c"],
            mode="lines",
            name="Min temperature",
            line=dict(color="#2563eb", width=2.8),
            hovertemplate="%{x|%d %b %Y}<br>%{y:.2f} °C",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=daily["datetime"],
            y=daily["temperature_max_c"],
            mode="lines",
            name="Max temperature",
            line=dict(color="#b45309", width=2.8),
            fill="tonexty",
            fillcolor="rgba(180, 83, 9, 0.10)",
            hovertemplate="%{x|%d %b %Y}<br>%{y:.2f} °C",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=daily["datetime"],
            y=daily["average_wind_ms"],
            yaxis="y2",
            mode="lines",
            name="Avg wind",
            line=dict(color="#0f766e", width=2.4, dash="dot"),
            hovertemplate="%{x|%d %b %Y}<br>%{y:.2f} m/s",
        )
    )
    fig.update_layout(
        title="Daily min/max temperature, rainfall, and average wind",
        yaxis=dict(title="Temperature / rainfall"),
        yaxis2=dict(
            title="Wind speed (m/s)",
            overlaying="y",
            side="right",
            showgrid=False,
            tickfont=dict(color=SECONDARY_TEXT_COLOR, size=12),
            title_font=dict(color=TEXT_COLOR, size=13),
            linecolor=BORDER_COLOR,
            zerolinecolor=BORDER_COLOR,
        ),
    )
    return apply_dashboard_layout(fig, height=420)


def create_correlation_heatmap(correlation_matrix: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        data=go.Heatmap(
            z=correlation_matrix.values,
            x=correlation_matrix.columns,
            y=correlation_matrix.index,
            zmin=-1,
            zmax=1,
            colorscale=[
                [0, "#1d4ed8"],
                [0.5, "#f8fafc"],
                [1, "#b45309"],
            ],
            colorbar=dict(
                title=dict(text="r", font=dict(color=TEXT_COLOR)),
                tickfont=dict(color=SECONDARY_TEXT_COLOR),
            ),
            hovertemplate="%{y} vs %{x}<br>r=%{z:.2f}<extra></extra>",
        )
    )
    fig.update_layout(title="Correlation heatmap")
    return apply_dashboard_layout(fig, height=430)


def create_correlation_scatter(
    data: pd.DataFrame,
    x_label: str,
    x_column: str,
    y_label: str,
    y_column: str,
) -> go.Figure:
    chart_data = data[[x_column, y_column]].dropna()
    correlation = chart_data[x_column].corr(chart_data[y_column]) if len(chart_data) > 1 else 0
    display_data = chart_data
    if len(display_data) > 3000:
        display_data = display_data.sample(3000, random_state=7).sort_index()

    fig = px.scatter(
        display_data,
        x=x_column,
        y=y_column,
        title=f"{x_label} vs {y_label} (r={correlation:.2f})",
        labels={x_column: x_label, y_column: y_label},
        opacity=0.58,
    )
    fig.update_traces(
        marker=dict(color="#2563eb", size=7, line=dict(color="#1e3a8a", width=0.5)),
        selector=dict(mode="markers"),
    )
    if len(chart_data) >= 3 and chart_data[x_column].nunique() > 1:
        x_values = chart_data[x_column].to_numpy()
        y_values = chart_data[y_column].to_numpy()
        slope, intercept = np.polyfit(x_values, y_values, 1)
        line_x = np.linspace(x_values.min(), x_values.max(), 80)
        line_y = slope * line_x + intercept
        fig.add_trace(
            go.Scatter(
                x=line_x,
                y=line_y,
                mode="lines",
                name="Trendline",
                line=dict(color="#b45309", width=3),
                hovertemplate="%{x:.2f}<br>%{y:.2f}<extra>Trendline</extra>",
            )
        )
    return apply_dashboard_layout(fig, height=430)


def create_comparison_chart(comparison: pd.DataFrame, metric_label: str, unit: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=comparison["month_name"],
            y=comparison["local_value"],
            mode="lines+markers",
            name="Local station average",
            line=dict(color="#2563eb", width=3),
            hovertemplate="%{x}<br>%{y:.2f} " + unit,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=comparison["month_name"],
            y=comparison["met_value"],
            mode="lines+markers",
            name="Bradford MET baseline",
            line=dict(color="#0f766e", width=3),
            hovertemplate="%{x}<br>%{y:.2f} " + unit,
        )
    )
    fig.add_bar(
        x=comparison["month_name"],
        y=comparison["difference"],
        name="Difference",
        marker_color="#f59e0b",
        opacity=0.32,
        hovertemplate="%{x}<br>%{y:+.2f} " + unit,
    )
    fig.update_layout(
        title=f"Local weather station vs Bradford MET monthly {metric_label.lower()}",
        yaxis_title=f"{metric_label} ({unit})",
    )
    return apply_dashboard_layout(fig, height=430)
