#!/bin/bash
# Production launch script for MindOS
# Usage: ./scripts/run_production.sh

cd "$(dirname "$0")/.." || exit

# Ensure we're on main branch
git checkout main

# Set production environment
export ENVIRONMENT=production

# Load environment variables from .env (production)
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run Streamlit on port 8501 with hot-reload disabled for stability
echo "🚀 Starting MindOS Production on http://localhost:8501"
echo "Environment: $ENVIRONMENT"
streamlit run app.py --server.port 8501 --server.runOnSave false

