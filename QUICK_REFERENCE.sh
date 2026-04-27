#!/bin/bash
# AgriChat Quick Reference Commands
# Copy and paste these commands for common tasks

# ============================================
# 1. LOCAL DEVELOPMENT
# ============================================

# Setup virtual environment (first time)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run interactive setup
python setup.py

# Start local development server
func start

# Test health endpoint (in another terminal)
curl http://localhost:7071/api/health

# Test webhook verification
curl "http://localhost:7071/api/webhook?hub.verify_token=agrichat_verify_token_dev&hub.challenge=test123"

# ============================================
# 2. NGROK TUNNELING (For WhatsApp Testing)
# ============================================

# Start ngrok tunnel to local function app
ngrok http 7071

# Output will show: https://abc123.ngrok.io
# Use this URL in WhatsApp webhook configuration

# ============================================
# 3. AZURE DEPLOYMENT
# ============================================

# Login to Azure
az login

# Create resource group
az group create --name agrichat-rg --location eastus

# Create storage account
az storage account create \
  --name agrichatstg \
  --resource-group agrichat-rg \
  --location eastus

# Create function app
az functionapp create \
  --resource-group agrichat-rg \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name agrichat-functions \
  --storage-account agrichatstg

# Deploy code to Azure
func azure functionapp publish agrichat-functions --build remote

# Set environment variables
az functionapp config appsettings set \
  --name agrichat-functions \
  --resource-group agrichat-rg \
  --settings \
  OPENAI_API_KEY="sk-proj-..." \
  WHATSAPP_PHONE_NUMBER_ID="..." \
  WHATSAPP_ACCESS_TOKEN="..." \
  WHATSAPP_VERIFY_TOKEN="agrichat_verify_prod" \
  OPENWEATHER_API_KEY="..." \
  COSMOS_CONNECTION_STRING="..."

# ============================================
# 4. TESTING & DEBUGGING
# ============================================

# Send test text message
curl -X POST http://localhost:7071/api/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "field": "messages",
        "value": {
          "messages": [{
            "from": "919876543210",
            "type": "text",
            "text": {"body": "When should I plant rice?"}
          }],
          "contacts": [{"wa_id": "919876543210"}]
        }
      }]
    }]
  }'

# View function logs (local)
# Check the terminal where func start is running

# View Azure logs
az functionapp log tail --name agrichat-functions --resource-group agrichat-rg

# Check environment variables
az functionapp config appsettings list \
  --name agrichat-functions \
  --resource-group agrichat-rg

# ============================================
# 5. DATABASE OPERATIONS
# ============================================

# Connect to Cosmos DB (via Azure Portal):
# 1. Go to https://portal.azure.com/
# 2. Find your Cosmos DB account
# 3. Click "Data Explorer"
# 4. Browse interactions

# Query interactions for specific farmer (via Python):
# python3
# from functions.cosmos_handler import get_farmer_history
# history = get_farmer_history("919876543210")
# print(history)

# Get farmer profile
# from functions.cosmos_handler import get_farmer_profile
# profile = get_farmer_profile("919876543210")
# print(profile)

# ============================================
# 6. MONITORING & HEALTH CHECKS
# ============================================

# Check function app health
curl https://agrichat-functions.azurewebsites.net/api/health

# Monitor live logs
az functionapp log tail --name agrichat-functions --resource-group agrichat-rg -f

# Get function app status
az functionapp show \
  --name agrichat-functions \
  --resource-group agrichat-rg

# List all running functions
az functionapp function list \
  --name agrichat-functions \
  --resource-group agrichat-rg

# ============================================
# 7. CONFIGURATION MANAGEMENT
# ============================================

# View local settings
cat local.settings.json

# View environment variables
cat .env

# Update local settings for testing
# Edit local.settings.json directly

# Regenerate .env from example
cp .env.example .env
# Then edit .env with your credentials

# ============================================
# 8. CLEANUP & TROUBLESHOOTING
# ============================================

# Deactivate virtual environment
deactivate

# Remove venv (if needed)
rm -rf venv

# Clear Azure Functions cache
rm -rf .python_packages

# Restart function app
az functionapp stop --name agrichat-functions --resource-group agrichat-rg
az functionapp start --name agrichat-functions --resource-group agrichat-rg

# Delete resource group (caution!)
az group delete --name agrichat-rg --yes

# ============================================
# 9. DEVELOPMENT WORKFLOW
# ============================================

# Quick local test cycle:
# 1. Make code changes
# 2. func start will auto-reload
# 3. Test with curl or WhatsApp webhook
# 4. Check logs in console

# Deployment workflow:
# 1. Test locally: func start
# 2. Test with curl: Send test messages
# 3. Deploy: func azure functionapp publish agrichat-functions
# 4. Verify: Check Azure logs and health endpoint
# 5. Test via WhatsApp

# ============================================
# 10. USEFUL LINKS
# ============================================

# Azure Portal: https://portal.azure.com/
# OpenAI Keys: https://platform.openai.com/api-keys
# OpenWeatherMap: https://openweathermap.org/api
# WhatsApp Dashboard: https://www.facebook.com/login/
# Meta App Dashboard: https://developers.facebook.com/apps/

# ============================================
# 11. ENVIRONMENT VARIABLES QUICK REFERENCE
# ============================================

# OPENAI_API_KEY=sk-proj-...
# WHATSAPP_PHONE_NUMBER_ID=123456789
# WHATSAPP_ACCESS_TOKEN=EAAxxx...
# WHATSAPP_VERIFY_TOKEN=agrichat_verify_token
# WHATSAPP_APP_SECRET=xxx...
# OPENWEATHER_API_KEY=xxx...
# COSMOS_CONNECTION_STRING=AccountEndpoint=...
# COSMOS_DB_NAME=agrichat
# COSMOS_CONTAINER_NAME=interactions

# ============================================
# 12. COMMON ERRORS & FIXES
# ============================================

# Error: "func: command not found"
# Fix: npm install -g azure-functions-core-tools@4

# Error: "Python version not supported"
# Fix: Use Python 3.9+ (check: python3 --version)

# Error: "Webhook verification failed"
# Fix: Check WHATSAPP_VERIFY_TOKEN matches configuration

# Error: "OpenAI API error"
# Fix: Verify API key is valid and has credits

# Error: "Connection timeout to Cosmos DB"
# Fix: Check connection string, firewall rules

# ============================================

# For more information, see:
# - README.md (Project overview)
# - SETUP_GUIDE.md (Step-by-step setup)
# - API_TESTING.md (Testing examples)
# - PROJECT_SUMMARY.md (Complete summary)
