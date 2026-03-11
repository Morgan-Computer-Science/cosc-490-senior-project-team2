#!/bin/bash
echo "Starting Presidential Decision Support System..."
echo "Checking for .env file..."
if [ ! -f .env ]; then
  echo "ERROR: .env file not found. Copy .env.example to .env and fill in your values."
  exit 1
fi
pip install -r requirements.txt -q
streamlit run app.py --server.port 8501
