#!/bin/bash
# Run Streamlit app with development environment variables
export APP_ENV=dev
set -a
source .env.dev
set +a
exec streamlit run app.py --server.port $STREAMLIT_SERVER_PORT
