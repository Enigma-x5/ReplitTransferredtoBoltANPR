#!/bin/bash
# This script helps set up environment variables for selfhost mode
# Run this to configure your Replit secrets

echo "Setting up environment variables for ANPR City - Selfhost Mode"
echo "================================================================"
echo ""
echo "Please add these secrets in Replit Secrets UI:"
echo ""
echo "MODE=selfhost"
echo "API_HOST=localhost"
echo "API_PORT=8000"
echo "REDIS_URL=redis://localhost:6379/0"
echo "CORS_ORIGINS=*"
echo "JWT_SECRET=$(openssl rand -base64 32)"
echo "ADMIN_EMAIL=admin@example.com"
echo "ADMIN_PASSWORD=admin123"
echo "ADMIN_USERNAME=admin"
echo ""
echo "Note: DATABASE_URL is already set by Replit PostgreSQL"
