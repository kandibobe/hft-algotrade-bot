#!/bin/bash
# Stoic Citadel - Automated Deployment Script with Health Check

# --- Configuration ---
# Use the production docker-compose file
COMPOSE_FILE="deploy/docker-compose.yml"
# Time to wait for services to stabilize before health check
WAIT_TIME=20

# --- Pre-flight Checks ---
echo "🚀 Starting deployment of Stoic Citadel..."

# Check for .env file
if [ ! -f ".env" ]; then
    echo "❌ Critical Error: .env file not found."
    echo "Please create it by copying .env.example and filling in your credentials."
    exit 1
fi

echo "✅ .env file found."

# --- Deployment ---

# 1. Build and start services in detached mode
echo "🏗️ Building and starting services..."
docker-compose -f "$COMPOSE_FILE" up -d --build

# Check if docker-compose command was successful
if [ $? -ne 0 ]; then
    echo "❌ Docker Compose failed to start."
    exit 1
fi

# 2. Wait for services to stabilize
echo "⏳ Waiting for services to stabilize (${WAIT_TIME}s)..."
sleep $WAIT_TIME

# 3. Run Health Check
echo "🔍 Running system health check..."
if python src/monitoring/health_check.py; then
    echo "✅ Deployment successful! System is healthy."
    
    # --- Display Access Information ---
    echo "---"
    echo "🔑 Access Credentials:"
    
    # Source .env file to get variables
    set -a
    source .env
    set +a

    echo "  - FreqUI Dashboard: http://localhost:${FREQUI_PORT:-3000}"
    echo "    - User: ${FREQTRADE_API_USERNAME:-stoic_admin}"
    echo "    - Pass: Check your .env file for FREQTRADE_API_PASSWORD"

    echo "  - Grafana Monitoring: http://localhost:${GRAFANA_PORT:-3001}"
    echo "    - User: ${GRAFANA_ADMIN_USER:-admin}"
    echo "    - Pass: ${GRAFANA_ADMIN_PASSWORD:-admin}"
    
    echo "---"
    echo "💡 Tip: Use 'docker-compose -f ${COMPOSE_FILE} logs -f' to monitor real-time logs."

else
    echo "❌ Health Check failed! Triggering rollback..."
    ./rollback.sh
    exit 1
fi
