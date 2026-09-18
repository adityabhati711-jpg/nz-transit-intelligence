# 🚌 NZ Transit Intelligence

A machine-learning and transit analytics project for **Auckland Transport** data.  
The system combines GTFS and realtime transit data, PostgreSQL analytics, a delay-prediction model, a FastAPI backend, and an interactive Streamlit dashboard.

## Live Project

- **Live Dashboard:** https://nz-transit-intelligence.streamlit.app
- **API Documentation:** https://nz-transit-intelligence.onrender.com/docs
- **API Base URL:** https://nz-transit-intelligence.onrender.com

> The API is hosted on Render's free tier, so the first request after a period of inactivity can take longer while the service wakes up.

---

## Project Overview

NZ Transit Intelligence was built to turn raw public-transport data into useful operational insights and a practical machine-learning prediction service.

The project can:

- load and organise Auckland Transport GTFS and realtime transit data;
- analyse route, stop, and time-period performance;
- identify routes and stops with higher observed delay rates;
- predict delay risk for a selected journey;
- expose predictions and analytics through a REST API;
- present the results through an interactive web dashboard.

The deployed application uses a cloud PostgreSQL database and a production FastAPI service, while the Streamlit frontend consumes the public API.

---

## Dashboard

![NZ Transit Intelligence dashboard](docs/images/dashboard.png)

The dashboard provides journey controls, delay prediction, network KPIs, route analytics, time-period analysis, problem-stop analysis, an interactive geographic map, and model metrics.

---

## Main Features

### Delay Prediction

Users can choose:

- route;
- direction;
- stop;
- hour of day;
- day of week.

The application returns:

- delay probability;
- risk level;
- delayed / not-delayed prediction;
- time period;
- prediction probability gauge;
- journey summary.

### Transit Network Analytics

The dashboard currently reports a snapshot including:

- **6,008** realtime observations;
- **3,660** unique trips;
- **283** observed routes;
- **1,370** observed stops.

It also displays average and median delay statistics, delayed percentage, and on-time percentage.

### Route and Time-Period Analysis

The project includes:

- routes with the highest observed delay rate;
- route-level observations and delay statistics;
- delay rate by time period;
- average delay by time period.

### Problem Stops

The system identifies stops with higher observed delay rates and displays:

- delayed percentage;
- observation count;
- average delay;
- maximum delay;
- an interactive Auckland map using stop coordinates.

### REST API

FastAPI exposes endpoints for prediction, GTFS data, and analytics.

![NZ Transit Intelligence API documentation](docs/images/api-docs.png)

Important endpoints include:

```text
GET  /health
GET  /model-info
POST /predict-delay
GET  /routes
GET  /gtfs/routes
GET  /gtfs/routes/{route_id}/stops
GET  /analytics/network-kpis
GET  /analytics/time-period-performance
GET  /analytics/top-delayed-routes
GET  /analytics/problem-stops
```

Interactive Swagger documentation is available at:

https://nz-transit-intelligence.onrender.com/docs

---

## Machine-Learning Model

The production prediction model is **Logistic Regression**.

Current evaluation metrics:

| Metric | Value |
|---|---:|
| Accuracy | 83.80% |
| ROC AUC | 0.635 |
| PR AUC | 0.151 |
| Precision | 0.171 |
| Recall | 0.233 |
| F1 Score | 0.198 |

The project exposes these metrics directly through the API and dashboard.

Accuracy is shown alongside precision, recall, F1, ROC AUC, and PR AUC because delay prediction is an imbalanced classification problem and accuracy alone does not describe performance completely.

---

## Architecture

```text
Auckland Transport Data
        │
        ├── GTFS static data
        └── Realtime transit observations
                    │
                    ▼
            Python ingestion pipeline
                    │
                    ▼
          PostgreSQL / Neon database
                    │
           ┌────────┴─────────┐
           ▼                  ▼
     Analytics views     Feature engineering
           │                  │
           │                  ▼
           │           Logistic Regression
           │                  │
           └────────┬─────────┘
                    ▼
               FastAPI API
            (deployed on Render)
                    │
                    ▼
          Streamlit Dashboard
      (Streamlit Community Cloud)
```

---

## Technology Stack

### Data and Machine Learning

- Python
- pandas
- scikit-learn
- joblib

### Database and Data Access

- PostgreSQL
- Neon serverless PostgreSQL
- SQLAlchemy
- psycopg

### Backend

- FastAPI
- Uvicorn
- REST API
- OpenAPI / Swagger

### Frontend and Visualisation

- Streamlit
- Plotly
- OpenStreetMap-based map visualisation

### Deployment and Development

- Render
- Streamlit Community Cloud
- Git
- GitHub
- Visual Studio Code

---

## Project Structure

```text
nz-transit-intelligence/
│
├── models/
│   └── final_delay_model.joblib
│
├── src/
│   ├── analytics/
│   ├── api/
│   │   └── main.py
│   ├── dashboard/
│   │   └── app.py
│   ├── ingestion/
│   ├── modeling/
│   ├── config.py
│   ├── database.py
│   └── schema.py
│
├── docs/
│   └── images/
│       ├── dashboard.png
│       └── api-docs.png
│
├── .env.example
├── .gitignore
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/adityabhati711-jpg/nz-transit-intelligence.git
cd nz-transit-intelligence
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root.

Example:

```env
AT_API_KEY=your_auckland_transport_api_key

DB_HOST=your_database_host
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
```

Do **not** commit the `.env` file or real credentials to GitHub.

### 5. Start the FastAPI backend

```bash
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/docs
```

### 6. Run the Streamlit dashboard against the local API

In a second PowerShell terminal:

```powershell
$env:API_URL="http://127.0.0.1:8000"
streamlit run src/dashboard/app.py
```

Streamlit will print the local dashboard URL in the terminal.

If `API_URL` is not set, the dashboard uses the deployed Render API by default.

---

## Deployment

### Backend API

The FastAPI application is deployed on **Render** and connects to the cloud PostgreSQL database hosted on **Neon**.

### Dashboard

The Streamlit dashboard is deployed through **Streamlit Community Cloud** and communicates with the public FastAPI service.

---

## Repository Workflow

The project uses:

- `develop` for active development;
- `main` for the stable production version.

Changes are tested before being promoted to `main`.

---

## Notes

This project is designed as an end-to-end data and machine-learning portfolio project, covering data ingestion, database design, analytics, machine learning, API development, visualisation, and cloud deployment.

For licensing information, see the `LICENSE` file.
