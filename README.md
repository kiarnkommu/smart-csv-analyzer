Smart CSV Analyzer

Project Overview

Smart CSV Analyzer is a Python-based web application that helps users upload, analyze, clean and visualize CSV datasets.

Technologies Used

- Python
- Streamlit
- Pandas
- NumPy
- Matplotlib
- FastAPI
- SQLite

Features

- Upload CSV files
- Preview datasets
- Identify missing values
- Detect duplicate records
- Generate data visualizations
- Clean datasets
- Download cleaned CSV files
- Store analysis history
- REST API integration

Project Architecture

1. Streamlit provides the user interface.
2. Pandas processes and analyzes CSV data.
3. Matplotlib generates charts.
4. SQLite stores analysis metadata.
5. FastAPI exposes REST API endpoints.

Installation

Install dependencies:

pip install -r requirements.txt

Run Streamlit

streamlit run app.py

Run FastAPI

uvicorn api:app --reload

API Documentation

Open:

http://127.0.0.1:8000/docs

Future Improvements

- React frontend integration
- PostgreSQL database
- User authentication
- Cloud deployment
- AI-powered data insights