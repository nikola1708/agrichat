# 🔌 Fonnte & Azure Integration Guide

Step-by-step guide untuk mengkoneksikan Fonnte WhatsApp API dengan Azure Functions.

---

## 1. Fonnte API Overview

### Apa itu Fonnte?
Fonnte adalah platform **WhatsApp Business API** yang memungkinkan bisnis mengirim/menerima pesan WhatsApp via API.

**Keuntungan untuk TaniWise:**
- ✅ Millions of Indonesian farmers already use WhatsApp
- ✅ No app download needed
- ✅ Real-time message delivery
- ✅ Webhook support for incoming messages
- ✅ Support for text, image, and location messages

### Fonnte URL & Endpoints
```
Panel: https://panel.fonnte.com
Base API: https://api.fonnte.com
Webhook: POST your-function-app.azurewebsites.net/api/fontte_webhook
```

---

## 2. Setup Fonnte Account

### Step 1: Register
1. Go to https://fonnte.com
2. Click "Daftar" (Register)
3. Fill form:
   - Email: your-email@example.com
   - Password: strong-password
   - Name: TaniWise Bot
4. Verify email
5. Login to panel

### Step 2: Connect WhatsApp Device
1. In Fonnte panel → Device Management
2. Click "Tambah Device" (Add Device)
3. Scan QR code with WhatsApp
4. Device will connect (status: **Connected**)
5. Note the **Device ID** (format: `device_12345...`)

### Step 3: Get API Token
1. Panel → Settings → API
2. Generate new API token
3. Copy token (format: `token_xxxxx...`)
4. **SAVE THIS** - you'll need it for Azure

### Step 4: Test Device
1. Send a test message to connected device
2. Should appear in Fonnte panel
3. Confirm device is working

✅ **Fonnte Setup Complete!**

---

## 3. Setup Azure Function App

### Step 1: Create Function App in Azure Portal

```
Resource Group: taniwise-rg
Function App Name: taniwise-bot-dev
Runtime: Python 3.11
Region: Southeast Asia (Jakarta)
Hosting Plan: Consumption
Storage Account: Create new
```

### Step 2: Configure Application Settings

Go to: Function App → Configuration → Application Settings

Add these variables:
```
FONNTE_API_TOKEN = <your-token-from-fonnte>
FONNTE_DEVICE_ID = <your-device-id-from-fonnte>
OPENAI_API_KEY = <your-azure-openai-key>
OPENAI_ENDPOINT = <your-azure-openai-endpoint>
...other settings...
```

### Step 3: Get Function URL

After deployment, get the webhook URL:

```
https://taniwise-bot-dev.azurewebsites.net/api/fontte_webhook
```

This is the URL you'll register with Fonnte.

---

## 4. Connection Architecture

```
┌─────────────────────────────────────────────────┐
│        FARMER (WhatsApp User)                    │
│        Sends: "Tanam apa sekarang?"              │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓ WhatsApp Message
┌─────────────────────────────────────────────────┐
│        FONNTE API (Cloud)                        │
│        Receives message                          │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓ Webhook POST
                  │ {sender, type, message}
                  │
┌─────────────────────────────────────────────────┐
│    AZURE FUNCTION (Your Webhook Handler)        │
│    http://localhost:7071/api/fontte_webhook     │
│                                                  │
│    1. Parse incoming JSON                       │
│    2. Call GPT-4o for recommendation            │
│    3. Call OpenWeatherMap for weather           │
│    4. Get market prices from PIHPS              │
│    5. Format response                           │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓ Call Fonnte API
                  │ POST /api/send
                  │ {target, message, device}
┌─────────────────────────────────────────────────┐
│        FONNTE API                               │
│        Sends response to WhatsApp               │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓ WhatsApp Message
┌─────────────────────────────────────────────────┐
│        FARMER (WhatsApp User)                    │
│        Receives: "Tanam PADI minggu depan..."   │
└─────────────────────────────────────────────────┘
```

---

## 5. Webhook Payload Format

### Incoming Message (Fonnte → Azure Function)

```json
{
  "sender": "628123456789",
  "type": "text|image|location",
  "message": "Tanam apa sekarang?",
  "media_url": "https://...",
  "latitude": -6.2088,
  "longitude": 106.8456,
  "timestamp": "2024-04-21 10:30:00"
}
```

### Outgoing Message (Azure Function → Fonnte)

**Text Message:**
```json
{
  "target": "628123456789",
  "message": "🌾 REKOMENDASI TANAM...",
  "device": "device_12345..."
}
```

**Image Message:**
```json
{
  "target": "628123456789",
  "image": "https://...",
  "caption": "Diagnosis hasil",
  "device": "device_12345..."
}
```

---

## 6. Configure Fonnte Webhook

### In Fonnte Panel:

1. **Login** to https://panel.fonnte.com
2. **Menu** → **Pengaturan** (Settings)
3. **Webhook** section
4. Set **Webhook URL**:
   ```
   https://taniwise-bot-dev.azurewebsites.net/api/fontte_webhook
   ```
5. Set **Method**: `POST`
6. (Optional) Add **Auth Header**:
   - Header Name: `Authorization`
   - Value: Your token
7. **Save** webhook

### Test Webhook:

In Fonnte panel:
1. Click **"Test Webhook"** button
2. Should return:
   ```json
   {"status": "success", "message": "Webhook processed"}
   ```
3. If error, check:
   - Azure Function URL is correct
   - Function is running (no errors in logs)
   - Firewall allows Fonnte servers

---

## 7. Message Flow Implementation

### In `function_app.py`:

```python
@app.route(route="fontte_webhook", methods=["POST"])
async def fontte_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """Webhook handler for Fonnte messages"""
    
    # 1. Parse incoming webhook
    req_json = req.get_json()
    phone = req_json.get("sender")
    message_type = req_json.get("type")
    
    # 2. Process based on type
    if message_type == "text":
        response = handle_text_message(phone, req_json.get("message"))
    elif message_type == "image":
        response = handle_image_message(phone, req_json.get("media_url"))
    elif message_type == "location":
        response = handle_location_message(
            phone,
            req_json.get("latitude"),
            req_json.get("longitude")
        )
    
    # 3. Send response back via Fonnte
    fonnte_client.send_text_message(phone, response)
    
    # 4. Return success to Fonnte
    return func.HttpResponse(
        json.dumps({"status": "success", "phone": phone}),
        status_code=200,
        mimetype="application/json"
    )
```

---

## 8. Testing Guide

### Test 1: Local Testing with curl

Start local function:
```bash
func start
```

Send test message:
```bash
curl -X POST http://localhost:7071/api/fontte_webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "628123456789",
    "type": "text",
    "message": "Tanam apa sekarang?"
  }'
```

Should return:
```json
{"status": "success", "message": "Webhook processed"}
```

### Test 2: Test Webhook in Fonnte Panel

1. Go to Fonnte panel → Pengaturan → Webhook
2. Click "Test Webhook" button
3. Fonnte sends test payload to your Azure Function
4. Check Azure logs (Application Insights) for errors

### Test 3: Send Real WhatsApp Message

1. Open WhatsApp on your phone
2. Message Fonnte-connected number
3. Message appears in Fonnte inbox
4. Webhook automatically triggered
5. Response sent back to WhatsApp

---

## 9. Common Issues & Solutions

### Issue: Webhook returns 403 Unauthorized

**Cause:** Wrong Fonnte credentials

**Solution:**
```python
# Check in function_app.py
if not self.api_token or not self.device_id:
    logger.error("Credentials missing!")
    return False
```

Verify in Azure Settings:
- [ ] `FONNTE_API_TOKEN` is correct
- [ ] `FONNTE_DEVICE_ID` is correct
- [ ] No typos/spaces

### Issue: No response in WhatsApp

**Cause:** Function error or wrong phone format

**Solution:**
1. Check phone number format: `628123456789` (not spaces, not +62)
2. Check Azure Function logs in Application Insights
3. Verify Fonnte device is connected

### Issue: Webhook not triggered

**Cause:** URL mismatch in Fonnte panel

**Solution:**
1. Copy exact URL from Azure Function:
   ```
   https://taniwise-bot-dev.azurewebsites.net/api/fontte_webhook
   ```
2. Paste in Fonnte Pengaturan → Webhook
3. Click Save
4. Test webhook button

### Issue: Message takes > 5 seconds

**Cause:** Slow GPT-4o API or network

**Solution:**
1. Optimize prompt (shorter)
2. Add response timeout in host.json
3. Cache weather/price data
4. Use faster models

---

## 10. API Quotas & Rate Limits

### Fonnte Limits
- **Free Tier:** 1000 messages/month
- **Paid Tier:** Unlimited (pay per message)
- **Rate Limit:** 100 requests/minute per device

### Azure OpenAI Limits
- **Standard:** 200 requests/minute
- **Higher quota:** Request increase in Azure

### OpenWeatherMap Limits
- **Free:** 1000 API calls/day
- **Paid:** Up to 1M+ calls/day

---

## 11. Security Best Practices

### 1. Secure Credentials
```bash
# Never commit credentials to GitHub
echo "local.settings.json" >> .gitignore

# Use Azure Key Vault for production
az keyvault create --name taniwise-vault --resource-group taniwise-rg
```

### 2. Validate Webhook Payload
```python
def validate_webhook_payload(payload):
    """Ensure payload comes from Fonnte"""
    required = ["sender", "type"]
    return all(field in payload for field in required)
```

### 3. Rate Limiting
```python
# Implement rate limiting per phone number
rate_limiter = {}  # {phone: [timestamp, timestamp, ...]}
```

### 4. CORS Configuration
In Azure Function → CORS:
- Add only Fonnte domain: `https://panel.fonnte.com`

---

## 12. Monitoring & Logs

### View Logs in Azure Portal
1. Function App → Application Insights → Logs
2. Query example:
   ```kusto
   traces
   | where message contains "fontte"
   | project timestamp, message, severity
   | order by timestamp desc
   ```

### Monitor in Real-Time
```bash
az functionapp log tail --name taniwise-bot-dev \
  --resource-group taniwise-rg
```

### Key Metrics to Track
- [ ] Response time (< 3 seconds)
- [ ] Error rate (< 1%)
- [ ] Message success rate (> 95%)
- [ ] Fonnte API uptime (99.9%)

---

## Reference

| Item | Value |
|------|-------|
| **Fonnte Panel** | https://panel.fonnte.com |
| **Fonnte API Docs** | https://fonnte.com/documentation |
| **Webhook Method** | POST |
| **Content-Type** | application/json |
| **Response Timeout** | 30 seconds |
| **Phone Format** | 628123456789 (no +, no spaces) |

---

**Last Updated:** 2024-04-21  
**Version:** 1.0
