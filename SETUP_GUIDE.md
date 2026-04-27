# AgriChat Setup Guide - Step by Step

## Phase 1: Local Development Setup (30 minutes)

### Step 1.1: Install Azure Functions Core Tools

**Windows/macOS/Linux**:
```bash
# Using npm (recommended)
npm install -g azure-functions-core-tools@4 --unsafe-perm=true --allow-root

# Or using Homebrew (macOS)
brew tap azure/tap && brew install azure-functions-core-tools@4
```

Verify installation:
```bash
func --version
```

### Step 1.2: Install Python Dependencies

```bash
cd agrichat
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### Step 1.3: Configure Local Settings

1. Copy environment template:
```bash
cp .env.example .env
```

2. Update `.env` with your credentials:
```
OPENAI_API_KEY=sk-proj-...your-key...
WHATSAPP_VERIFY_TOKEN=agrichat_verify_token_dev
OPENWEATHER_API_KEY=your-key-here
```

3. Update `local.settings.json` with the same values

### Step 1.4: Run Locally

```bash
func start
```

You should see:
```
Azure Functions Core Tools
Version: 4.x.x
Listening on 'http://localhost:7071'
Functions loaded...
```

### Step 1.5: Test Webhook Endpoint

Open a new terminal and test:

```bash
# Test webhook verification
curl "http://localhost:7071/api/webhook?hub.verify_token=agrichat_verify_token_dev&hub.challenge=test123"
# Should return: test123

# Test health endpoint
curl http://localhost:7071/api/health
# Should return JSON with status: "healthy"
```

## Phase 2: Get Required API Keys (30-60 minutes)

### 2.1: OpenAI API Key ✅ (Already Have)

You already provided: `sk-proj-64FOBjqMH7s...`

Test the key:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-proj-64FOBjqMH7s..." \
  -H "Content-Type: application/json"
```

### 2.2: OpenWeatherMap API Key

1. Go to https://openweathermap.org/api
2. Sign up for free account
3. Get your API key from account settings
4. Free tier includes:
   - Current weather
   - 5-day forecast
   - 60 calls/minute limit

Test:
```bash
curl "https://api.openweathermap.org/data/2.5/weather?q=Delhi&appid=YOUR_KEY&units=metric"
```

### 2.3: WhatsApp Business API Setup (For Testing)

You have options:

**Option A: Using WhatsApp Cloud API Sandbox** (Free Testing)
1. Create Meta Business Account: https://business.facebook.com
2. Set up WhatsApp App in Meta App Dashboard
3. Get test phone number ID and access token
4. Add your personal WhatsApp number to test recipients

**Option B: WhatsApp Business Account** (Production)
1. Apply for WhatsApp Business API
2. Get verified business account
3. Get production phone number ID and access token

**For MVP Testing**: Use Option A (Sandbox)

Steps:
1. Go to https://www.facebook.com/login/
2. Create Business Account
3. Go to App Dashboard
4. Create new WhatsApp App
5. Copy:
   - Phone Number ID
   - Access Token
   - App Secret

### 2.4: Azure Cosmos DB (Optional for MVP)

If using Cosmos DB:

1. Create Azure account (Student or Free)
2. Create Cosmos DB account
3. Create database: "agrichat"
4. Create container: "interactions" (Partition key: "/phone_number")
5. Copy connection string

For MVP without Cosmos DB:
- System will log to console instead
- Interaction history won't persist
- Remove Cosmos DB calls or return empty history

## Phase 3: Local Testing with WhatsApp Sandbox (30 minutes)

### 3.1: Configure Webhook

In Meta App Dashboard:

1. Go to WhatsApp → Configuration
2. Set **Callback URL**:
   - **Local Testing**: Use ngrok tunnel (see below)
   - **Production**: Your Azure Function URL

3. Set **Verify Token**: `agrichat_verify_token_dev`

4. Subscribe to: `messages` webhook

### 3.2: Use ngrok for Local Testing

```bash
# Install ngrok from https://ngrok.com/download

# Start ngrok tunnel to local function app
ngrok http 7071

# You'll get a URL like: https://abc123.ngrok.io
```

Then in Meta App Dashboard, set Callback URL:
```
https://abc123.ngrok.io/api/webhook
```

### 3.3: Send Test Message

1. In Meta App Dashboard, go to WhatsApp → Sandbox
2. Scan QR code with your WhatsApp app
3. Send message to number: `+1 555 123 4567`

You should see:
- Message logged in `func start` console
- Response sent back to your WhatsApp

## Phase 4: Deploy to Azure (45 minutes)

### 4.1: Create Azure Resources

```bash
# Login
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
  --name agrichat-<your-name> \
  --storage-account agrichatstg
```

### 4.2: Deploy Code

```bash
# From project root
func azure functionapp publish agrichat-<your-name> --build remote
```

### 4.3: Configure Production Settings

```bash
# Set environment variables in Azure
az functionapp config appsettings set \
  --name agrichat-<your-name> \
  --resource-group agrichat-rg \
  --settings \
  OPENAI_API_KEY="sk-proj-..." \
  WHATSAPP_PHONE_NUMBER_ID="your-id" \
  WHATSAPP_ACCESS_TOKEN="your-token" \
  WHATSAPP_VERIFY_TOKEN="agrichat_verify_token_prod" \
  OPENWEATHER_API_KEY="your-key" \
  COSMOS_CONNECTION_STRING="your-connection-string"
```

### 4.4: Configure WhatsApp Webhook (Production)

In Meta App Dashboard:

1. Change Callback URL to:
   ```
   https://agrichat-<your-name>.azurewebsites.net/api/webhook
   ```

2. Change Verify Token to production value

3. Subscribe to messages and other events

## Phase 5: Testing & Validation (20 minutes)

### 5.1: Health Check

```bash
# Check if function is running
curl https://agrichat-<your-name>.azurewebsites.net/api/health
```

### 5.2: Monitor Logs

**Azure Portal**:
1. Go to your function app
2. Click "Log Stream"
3. Send test messages

**CLI**:
```bash
az functionapp log tail \
  --name agrichat-<your-name> \
  --resource-group agrichat-rg
```

### 5.3: Test with Real WhatsApp (if production setup)

1. Verify your WhatsApp Business account
2. Send test messages to your number
3. Check responses

## Phase 6: Cost Optimization & Production Setup (Optional)

### 6.1: Monitor Costs

```bash
# View your spending
az consumption usage list --resource-group agrichat-rg
```

### 6.2: Enable Cosmos DB (if needed)

```bash
# Create Cosmos DB account
az cosmosdb create \
  --resource-group agrichat-rg \
  --name agrichat-cosmos \
  --kind GlobalDocumentDB
```

### 6.3: Add Custom Domain (Optional)

```bash
# Bind custom domain
az functionapp config ssl create \
  --name agrichat-<your-name> \
  --resource-group agrichat-rg \
  --certificate-file path/to/cert.pfx \
  --certificate-password password
```

## Troubleshooting Guide

### Issue: "func not recognized"
**Solution**: Add npm bin to PATH or use `npx func` instead

### Issue: Webhook verification fails
**Solution**: 
1. Check Verify Token matches (case-sensitive)
2. Ensure function is running
3. Check URL is publicly accessible
4. For local: Use ngrok and correct ngrok URL

### Issue: OpenAI API errors
**Solution**:
1. Test key with: `curl https://api.openai.com/v1/models -H "Authorization: Bearer YOUR_KEY"`
2. Check you have API credits
3. Verify organization access

### Issue: Cosmos DB connection fails
**Solution**:
1. Copy connection string correctly (no extra spaces)
2. Check firewall rules allow your IP
3. Verify container exists
4. Check database name and container name

### Issue: WhatsApp message not received
**Solution**:
1. Verify webhook is receiving requests (check logs)
2. Check webhook signature verification
3. Ensure phone number format is correct
4. Verify phone number is in sandbox recipients list

### Issue: Local testing works but Azure doesn't
**Solution**:
1. Check all environment variables are set in Azure
2. Verify Azure Function Runtime is Python 3.11
3. Check application logs in Azure portal
4. Ensure all dependencies in requirements.txt

## Next Steps

1. ✅ Complete Phase 1 (Local Setup)
2. ✅ Complete Phase 2 (Get API Keys)
3. ✅ Test with Phase 3 (Local Testing)
4. Deploy to Azure (Phase 4)
5. Configure Production (Phase 5)

## Support

For issues:
1. Check function logs: `az functionapp log tail`
2. Review error messages
3. Check API key validity
4. Verify webhook configuration

Good luck! 🌾🚀
