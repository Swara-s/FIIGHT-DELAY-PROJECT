# AI-Powered Flight Delay Prediction System

A professional final-year major project built with Flask, SQLite, Bootstrap, and Scikit-learn.

## Features
- Modern responsive multi-page UI (Home, About, Predict, Dashboard, Result, Contact)
- Login/Register authentication with session management
- Role support (`admin` + `user`)
- ML pipeline with:
  - Random Forest classifier
  - Optional XGBoost classifier (if available)
  - Linear Regression for delay-minute estimation
- Prediction confidence score and delay probability
- Dashboard analytics with Chart.js (bar, pie, line)
- SQLite storage for users and prediction history
- REST APIs for prediction and dashboard data

## Project Structure
```text
dy patil/
├── app.py
├── requirements.txt
├── backend/
├── templates/
├── static/
├── dataset/
├── model/
├── database/
├── frontend/
├── screenshots/
└── documentation/
```

## Setup Instructions
1. Create virtual environment (optional):
   - `python -m venv .venv`
   - `.venv\Scripts\activate` (Windows)
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run the application:
   - `python app.py`
4. Open browser:
   - `http://127.0.0.1:5000`

## How Model Training Works
- On first run, the app trains models automatically using `dataset/flights_data.csv`.
- It saves model files into `model/`.
- Admin users can retrain model using dashboard button.

## API Endpoints
- `POST /api/predict` - JSON prediction endpoint (login required)
- `GET /api/dashboard-data` - dashboard statistics and chart data
- `POST /api/retrain-model` - retrain model (admin only)

## Submission Notes
- Add your screenshots to the `screenshots/` folder.
- Zip the complete project folder after running once so model and DB files are included.
