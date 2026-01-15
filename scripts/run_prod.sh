#!/usr/bin/env bash
set -euo pipefail

cd "/Users/anshulkiyawat/Projects/MindOS"

# Activate venv (adjust if you use a different env)
source "venv/bin/activate"

# Load prod env vars
set -a
source ".env.prod"
set +a

# Run Streamlit
exec streamlit run app.py \
  --server.port "${STREAMLIT_SERVER_PORT:-8501}" \
  --server.headless true
