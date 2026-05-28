# Project Explanation

## Title
AI-Powered Flight Delay Prediction System Using Historical and Real-Time Data

## Objective
To build a full-stack web application that predicts whether a flight is likely to be delayed and estimates delay minutes using machine learning.

## Modules
1. Authentication module (register/login/session/roles)
2. Flight prediction module (form + API + model inference)
3. Dashboard analytics module (stats + charts)
4. Data persistence module (SQLite history and users)
5. ML lifecycle module (training, evaluation, serialization)

## ML Workflow
- Dataset: `dataset/flights_data.csv`
- Preprocessing: missing value handling + one-hot encoding
- Models:
  - Random Forest Classifier
  - Optional XGBoost Classifier (if package installed)
  - Linear Regression for delay-minutes estimation
- Evaluation:
  - Classification: F1 score and accuracy
  - Regression: Mean Absolute Error (MAE)
- Persistence: pickle files in `model/`

## Future Scope
- Live weather API integration
- Real airline schedule APIs
- Deployment on cloud with CI/CD
