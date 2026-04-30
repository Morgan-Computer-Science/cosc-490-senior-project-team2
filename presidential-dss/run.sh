#!/bin/bash

echo "=== Presidential Decision Support System ==="

# ── Step 1: Install gcloud if not present ─────────────────────
if ! command -v gcloud &> /dev/null; then
    echo "Google Cloud CLI not found. Installing..."
    curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz
    tar -xf google-cloud-cli-linux-x86_64.tar.gz
    ./google-cloud-sdk/install.sh --quiet
    source ~/.bashrc
    source ./google-cloud-sdk/path.bash.inc
    rm -f google-cloud-cli-linux-x86_64.tar.gz
    echo "Google Cloud CLI installed."
else
    echo "Google Cloud CLI already installed."
fi

# ── Step 2: Check authentication ──────────────────────────────
if ! gcloud auth application-default print-access-token &> /dev/null; then
    echo ""
    echo "You need to authenticate with Google Cloud."
    gcloud init
    gcloud auth application-default login
else
    echo "Already authenticated with Google Cloud."
fi

# ── Step 3: Set project ───────────────────────────────────────
gcloud config set project presidential-dss 2>/dev/null

# ── Step 4: Check .env file ───────────────────────────────────
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "Please edit .env and set your GOOGLE_CLOUD_PROJECT then rerun this script."
    exit 1
fi

# ── Step 5: Install Python dependencies ──────────────────────
echo "Installing dependencies..."
pip install -r requirements.txt -q

# ── Step 6: Clear Python cache ───────────────────────────────
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

# ── Step 7: Launch the app ────────────────────────────────────
echo ""
echo "Starting app on port 8501..."
echo "Go to the Ports tab and open port 8501 in your browser."
echo ""
streamlit run app.py --server.port 8501