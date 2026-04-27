# 🚀 TaniWise Bot - Setup Checklist

Complete guide untuk setup TaniWise Bot dari 0 sampai live.

---

## ✅ Phase 1: Local Development Setup (30 menit)

### 1.1 Clone & Install
- [ ] Clone repository: `git clone <repo-url>`
- [ ] Navigate to folder: `cd taniwise-bot`
- [ ] Create venv: `python -m venv venv`
- [ ] Activate venv: `source venv/bin/activate` (macOS/Linux) or `venv\Scripts\activate` (Windows)
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Install Azure Functions Core Tools: `pip install azure-functions-core-tools --pre`

### 1.2 Configure Local Environment
- [ ] Copy template: `cp local.settings.json.template local.settings.json`
- [ ] Edit `local.settings.json` with dummy values for initial testing:
  ```json
  {
    "COSMOS_CONNECTION_STRING": "test-connection",
    "OPENAI_API_KEY": "test-key",
    ...
  }
  ```

### 1.3 Run Locally
- [ ] Start function: `func start`
- [ ] Should see: `Azure Functions Core Tools started successfully`
- [ ] Test health endpoint: `curl http://localhost:7071/api/health`
- [ ] Should return `{"status": "healthy", ...}`

✅ **Checkpoint:** Local server running

---

## ✅ Phase 2: Azure Resources Setup (1-2 jam)

### 2.1 Create Azure Resources

#### Cosmos DB
- [ ] Go to Azure Portal
- [ ] Create Cosmos DB account:
  - [ ] Account name: `taniwise-prod-db`
  - [ ] API: Core (SQL)
  - [ ] Location: Southeast Asia (Jakarta)
  - [ ] Capacity mode: Serverless (for MVP)
- [ ] Wait for deployment (5 min)
- [ ] Go to Keys → Copy CONNECTION STRING
- [ ] Update `local.settings.json` → `COSMOS_CONNECTION_STRING`

#### Azure OpenAI
- [ ] Create Azure OpenAI resource:
  - [ ] Name: `taniwise-openai`
  - [ ] Location: East US (or available region)
  - [ ] Tier: Standard (S0)
- [ ] Deploy GPT-4 model:
  - [ ] Go to Deployments → Create new deployment
  - [ ] Model: gpt-4
  - [ ] Deployment name: `gpt-4`
  - [ ] Version: latest
- [ ] Copy:
  - [ ] API Key → `OPENAI_API_KEY`
  - [ ] Endpoint → `OPENAI_ENDPOINT`

#### Azure Computer Vision (Optional for MVP)
- [ ] Create Computer Vision resource:
  - [ ] Name: `taniwise-vision`
  - [ ] Location: Southeast Asia
  - [ ] Tier: Standard (S1)
- [ ] Copy API Key → `AZURE_VISION_KEY`
- [ ] Copy Endpoint → `AZURE_VISION_ENDPOINT`

### 2.2 Get External API Keys

#### OpenWeatherMap
- [ ] Go to https://openweathermap.org
- [ ] Sign up (free tier)
- [ ] Get API Key → `OPENWEATHERMAP_API_KEY`
- [ ] Update local.settings.json

#### Fonnte WhatsApp API
- [ ] Go to https://fonnte.com
- [ ] Sign up (register with business account)
- [ ] Get API Token → `FONNTE_API_TOKEN`
- [ ] Get Device ID → `FONNTE_DEVICE_ID`
- [ ] Update local.settings.json

### 2.3 Update Local Settings
- [ ] Open `local.settings.json`
- [ ] Fill in ALL credentials:
  ```json
  {
    "COSMOS_CONNECTION_STRING": "<from Cosmos DB Keys>",
    "COSMOS_DATABASE_ID": "taniwise-prod",
    "OPENAI_API_KEY": "<from Azure OpenAI>",
    "OPENAI_ENDPOINT": "<from Azure OpenAI>",
    "OPENAI_MODEL": "gpt-4",
    "FONNTE_API_TOKEN": "<from Fonnte panel>",
    "FONNTE_DEVICE_ID": "<from Fonnte panel>",
    "AZURE_VISION_KEY": "<from Azure Vision>",
    "AZURE_VISION_ENDPOINT": "<from Azure Vision>",
    "OPENWEATHERMAP_API_KEY": "<from OpenWeatherMap>"
  }
  ```

✅ **Checkpoint:** All credentials configured

---

## ✅ Phase 3: Test Webhook Locally (20 menit)

### 3.1 Start Local Server
- [ ] Run: `func start`
- [ ] Note the webhook URL (should be `http://localhost:7071/api/fonnte_webhook`)

### 3.2 Test Text Message
```bash
curl -X POST http://localhost:7071/api/fontte_webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "628123456789",
    "type": "text",
    "message": "Tanam apa sekarang?"
  }'
```
- [ ] Should return: `{"status": "success", ...}`
- [ ] Check console logs for messages

### 3.3 Test Image Message
```bash
curl -X POST http://localhost:7071/api/fontte_webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "628123456789",
    "type": "image",
    "media_url": "https://upload.wikimedia.org/wikipedia/commons/..."
  }'
```
- [ ] Should return success
- [ ] Check AI response

### 3.4 Test Location Message
```bash
curl -X POST http://localhost:7071/api/fontte_webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "628123456789",
    "type": "location",
    "latitude": -6.2088,
    "longitude": 106.8456
  }'
```
- [ ] Should return success with weather info

✅ **Checkpoint:** All message types work locally

---

## ✅ Phase 4: Deploy to Azure (30 menit)

### 4.1 Create Azure Function App
- [ ] Create resource: Function App
  - [ ] Name: `taniwise-bot-dev`
  - [ ] Runtime: Python 3.11
  - [ ] Region: Southeast Asia
  - [ ] Storage account: Create new
- [ ] Wait for deployment

### 4.2 Configure Application Settings
- [ ] Go to Function App → Configuration
- [ ] Add ALL application settings (copy from local.settings.json):
  - [ ] COSMOS_CONNECTION_STRING
  - [ ] COSMOS_DATABASE_ID
  - [ ] OPENAI_API_KEY
  - [ ] OPENAI_ENDPOINT
  - [ ] OPENAI_MODEL
  - [ ] FONNTE_API_TOKEN
  - [ ] FONNTE_DEVICE_ID
  - [ ] AZURE_VISION_KEY
  - [ ] AZURE_VISION_ENDPOINT
  - [ ] OPENWEATHERMAP_API_KEY
- [ ] Save all settings

### 4.3 Deploy Code
- [ ] Login to Azure: `az login`
- [ ] Deploy: `az functionapp publish taniwise-bot-dev`
- [ ] Wait for deployment (2-5 min)
- [ ] Get function URL from output

### 4.4 Enable CORS (if needed)
- [ ] Go to Function App → CORS
- [ ] Add allowed origins: `https://panel.fonnte.com`

✅ **Checkpoint:** Function deployed to Azure

---

## ✅ Phase 5: Connect Fonnte (15 menit)

### 5.1 Get Azure Function URL
- [ ] Go to Function App → Functions → fontte_webhook
- [ ] Copy function URL (format: `https://taniwise-bot-dev.azurewebsites.net/api/fontte_webhook`)

### 5.2 Configure Fonnte Webhook
- [ ] Go to https://panel.fonnte.com
- [ ] Menu → Pengaturan (Settings)
- [ ] Find "Webhook" section
- [ ] Set URL: `https://taniwise-bot-dev.azurewebsites.net/api/fontte_webhook`
- [ ] Set Method: POST
- [ ] Save settings

### 5.3 Test Webhook Connection
- [ ] In Fonnte panel, click "Test Webhook"
- [ ] Should return: `{"status": "success", ...}`
- [ ] Check Application Insights logs in Azure Portal

### 5.4 Add Test WhatsApp Number
- [ ] Get a test WhatsApp number (use your own or team member's)
- [ ] In Fonnte, make sure device is connected
- [ ] Save device ID in Azure Function settings

✅ **Checkpoint:** Fonnte connected to Azure Function

---

## ✅ Phase 6: End-to-End Test (15 menit)

### 6.1 Send Test Messages via WhatsApp
- [ ] Open WhatsApp
- [ ] Go to Fonnte contact
- [ ] Send text: "Tanam apa sekarang?"
- [ ] Should receive farming recommendation within 3 seconds

### 6.2 Send Photo for Diagnosis
- [ ] Take/find photo of healthy or diseased plant
- [ ] Send via WhatsApp
- [ ] Should receive plant diagnosis within 5 seconds

### 6.3 Send Location
- [ ] Share location via WhatsApp
- [ ] Should receive weather info for that location

### 6.4 Check Logs
- [ ] Go to Function App → Application Insights
- [ ] Filter logs by timestamp
- [ ] Verify all requests are logged

✅ **Checkpoint:** End-to-end working!

---

## ✅ Phase 7: Monitoring & Maintenance

### 7.1 Setup Alerts
- [ ] Go to Function App → Alerts
- [ ] Create alert for:
  - [ ] Function execution failures
  - [ ] Response time > 5 seconds
  - [ ] HTTP 5xx errors
- [ ] Set email notifications

### 7.2 Monitor Performance
- [ ] Check Application Insights regularly
- [ ] Monitor:
  - [ ] Response times (target < 3 sec)
  - [ ] Error rates (target < 1%)
  - [ ] Request volume
  - [ ] Cosmos DB usage

### 7.3 Scaling Configuration
- [ ] Function App → Scale up
- [ ] Set to "Consumption" plan (auto-scaling)
- [ ] Monitor costs in Cost Management

✅ **Checkpoint:** Monitoring in place

---

## ⚠️ Troubleshooting

### Webhook returns 403 Unauthorized
- [ ] Check `FONNTE_API_TOKEN` is correct
- [ ] Check `FONNTE_DEVICE_ID` is correct
- [ ] Verify Fonnte account is active

### Cosmos DB connection error
- [ ] Verify `COSMOS_CONNECTION_STRING` format
- [ ] Check Cosmos DB account is running
- [ ] Verify firewall allows Azure services

### GPT-4o timeout
- [ ] Check `OPENAI_API_KEY` is valid
- [ ] Check quota/limits in Azure OpenAI
- [ ] Increase timeout in host.json

### No response from Fonnte
- [ ] Check webhook URL in Fonnte panel
- [ ] Test with `curl` to verify endpoint works
- [ ] Check Application Insights logs
- [ ] Verify phone number format (628xxxxx)

### Diagnosis not working
- [ ] Check image URL is publicly accessible
- [ ] Verify `AZURE_VISION_KEY` is configured
- [ ] Check image size < 20MB

---

## 📊 Cost Estimation (Monthly)

| Service | Usage | Cost |
|---------|-------|------|
| Azure Functions | 1M requests | ~$15 |
| Cosmos DB | Serverless | ~$10-50 |
| Azure OpenAI | 100K tokens | ~$20 |
| Azure Computer Vision | 100 images | ~$2 |
| OpenWeatherMap | 1M calls | Free |
| Fonnte API | 1000 messages | ~$5-20 |
| **TOTAL** | | **~$50-100** |

---

## 🎯 Next Steps

After Phase 6:

1. **Collect User Feedback** - Test with actual farmers
2. **Optimize Prompts** - Refine GPT-4o prompts based on feedback
3. **Add Historical Data** - Build database of successful recommendations
4. **Expand to More Crops** - Add more commodities to price tracking
5. **Multi-Language Support** - Add regional languages (Sundanese, Javanese, etc.)
6. **Mobile App** - Build companion Android/iOS app
7. **Analytics Dashboard** - Track usage patterns and ROI

---

**Status:** 🔄 In Progress  
**Last Updated:** 2024-04-21  
**Maintained By:** TaniWise Team
