#!/bin/bash
# Development launch script for MindOS
# Usage: ./scripts/run_development.sh

cd "$(dirname "$0")/.." || exit

# Switch to development branch
git checkout development

# Set development environment
export ENVIRONMENT=development

# Load environment variables from .env.development if it exists, otherwise .env
if [ -f .env.development ]; then
    export $(cat .env.development | grep -v '^#' | xargs)
    echo "📝 Loaded .env.development"
elif [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "📝 Loaded .env (create .env.development for dev-specific settings)"
fi

# Run Streamlit on port 8502 with hot-reload enabled
echo "🔧 Starting MindOS Development on http://localhost:8502"
echo "Environment: $ENVIRONMENT"
streamlit run app.py --server.port 8502

