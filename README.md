# Bradford Weather Intelligence

A polished Streamlit portfolio dashboard for live Bradford weather monitoring and historical weather-station analysis. The app combines an Open-Meteo live feed with a historical University of Bradford station CSV, interactive Plotly visualisations, live weather alerts, correlation analysis, and Bradford MET comparison analytics.

## Features

- Live Bradford weather summary from Open-Meteo
- Live weather alerts based only on Open-Meteo current conditions
- Latest available historical University of Bradford station reading
- Interactive historical trend chart with metric and timeframe filters
- Timeframe options: last 7 days, last month, last year, and all time
- Historical daily conditions overview with min/max temperature, rainfall, and wind
- Historical metric correlation heatmap and pairwise scatter analysis
- Bradford MET monthly comparison analytics where matched baseline data exists
- Robust CSV cleaning, timestamp parsing, validation, and missing-data handling
- Graceful fallback when Open-Meteo is unavailable
- Clean responsive dashboard UI suitable for portfolio deployment

## Tech Stack

- Python
- Streamlit
- Pandas
- Plotly
- Requests
- CSV weather datasets

## Data Sources

- **Open-Meteo live feed:** used for live Bradford weather summary and live weather alerts.
- **Historical University of Bradford station CSV:** used for historical readings, timeframe filtering, trends, daily overview, and correlation analysis.
- **Bradford MET baseline CSV:** used for monthly comparison analytics where matching MET columns are available.

Only Open-Meteo values are labelled as live/current. Historical CSV values are labelled as historical station dataset readings.

## Project Structure

```text
weather-dashboard-portfolio/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   ├── sample_weather_data.csv
│   └── met_data.csv
├── assets/
│   └── screenshots/
└── utils/
    ├── __init__.py
    ├── charts.py
    ├── data_loader.py
    └── filters.py
```

## Run Locally

```bash
cd weather-dashboard-portfolio
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

On Windows PowerShell:

```powershell
cd weather-dashboard-portfolio
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Deployment Notes

For Replit or hosted environments:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

For Streamlit Community Cloud:

1. Push this project folder to GitHub.
2. Set `app.py` as the main Streamlit file.
3. Keep `requirements.txt` in the repository root.
4. Ensure publishable datasets are stored in `data/`.

## Screenshots

Add final screenshots before publishing:

```markdown
![Dashboard overview](assets/screenshots/dashboard-overview.png)
![Historical trend chart](assets/screenshots/historical-trend-chart.png)
![Correlation analysis](assets/screenshots/correlation-analysis.png)
![MET comparison](assets/screenshots/met-comparison.png)
```

## Known Limitations

- Open-Meteo availability depends on network access.
- Alert thresholds are simple demo thresholds, not official weather warnings.
- The included station CSV is historical, so dataset charts are not live.
- The current MET file provides matched monthly temperature baseline data; other comparison metrics show a friendly unavailable message unless matching MET columns are added.
- The timeframe filter is anchored to the latest timestamp in the historical CSV.

## Future Improvements

- Add automated tests for data loading, validation, and timeframe filtering.
- Add export buttons for filtered CSV data and chart images.
- Add optional deployment screenshots and a live portfolio URL.
- Add more MET baseline metrics if suitable public datasets are available.
- Add a short methodology note explaining station location, units, and assumptions.

## Deployment Checklist

- Do not commit `.venv/`, cache folders, private datasets, or university marking files.
- Replace or anonymise data before publishing if the CSV is not approved for public use.
- Add screenshots to `assets/screenshots/`.
- Confirm the live deployed app can reach Open-Meteo.
