# 🌾 TaniWise Bot - Telegram AI Assistant untuk Petani Indonesia

Pranata Mangsa adalah asisten keputusan berbasis **Telegram** yang membantu petani kecil Indonesia menentukan apa, kapan, dan bagaimana menanam berdasarkan prediksi harga, cuaca, dan diagnosis lahan real-time.

---

## 🎯 Problem & Solution

### Problem
- **87% petani Indonesia adalah petani gurem** (lahan < 0,5 hektar) dengan keterbatasan akses informasi
- **73% petani membuat keputusan tanam berdasarkan tetangga mereka**, bukan data pasar
- Hasil: Oversupply periodik → **harga jatuh 60-80% saat panen raya**
- El Niño 2026 memprediksi gagal panen masif → Perlu prediksi cuaca & rekomendasi

### Solution
**Pranata mangsa** = WhatsApp Bot + AI Reasoning + Real-time Data

- 📱 **No App Download** — Pakai WhatsApp yang sudah ada
- 🤖 **AI-Powered Recommendations** — GPT-4o untuk analisis harga + cuaca + kondisi lahan
- 🔍 **Plant Disease Diagnosis** — Foto WhatsApp → Azure Custom Vision + GPT-4o Vision
- ⚠️ **Weather Alerts** — Notifikasi cuaca ekstrem otomatis
- 📊 **Decision Infrastructure** — Cosmos DB centralized untuk big data pertanian nasional

---

## ✨ Features

| Fitur | Deskripsi | Tech |
|-------|-----------|------|
| 💬 **Text Chat** | Tanya "Tanam apa sekarang?" → Rekomendasi spesifik | GPT-4o |
| 📸 **Plant Diagnosis** | Kirim foto tanaman → Deteksi penyakit + solusi | Azure Vision + GPT-4o Vision |
| 🌤️ **Weather Alerts** | Notifikasi cuaca ekstrem otomatis | OpenWeatherMap API |
| 💰 **Price Tracking** | Harga pasar real-time per komoditas | PIHPS API |
| 📍 **Geo-Tagging** | Simpan lokasi → Rekomendasi spesifik per zona | Cosmos DB |
| 📊 **Historical Memory** | Tracking riwayat tanam & performa | Cosmos DB |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PETANI (WhatsApp User)                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓ Telegram Bot Webhook
┌─────────────────────────────────────────────────────────────┐
│               AZURE FUNCTIONS (Serverless)                   │
│         telegram_webhook - Main Handler                      │
└──────┬─────────────────────────────────────────────┬────────┘
       ↓                                              ↓
   ┌────────────────────┐      ┌──────────────────────────┐
   │  Text Handler      │      │  Image Handler           │
   │  (GPT-4o)          │      │  (Custom Vision +        │
   │                    │      │   GPT-4o Vision)         │
   └────────────────────┘      └──────────────────────────┘
       ↓                                  ↓
   ┌────────────────────────────────────────────────┐
   │   Data Integration Layer                       │
   │ - OpenWeatherMap (Cuaca)                       │
   │ - PIHPS API (Harga)                            │
   │ - BPS Data (Historical)                        │
   └────────────────────────────────────────────────┘
       ↓
   ┌────────────────────────────────────────────────┐
   │   COSMOS DB (NoSQL)                            │
   │ - petani (profile + history)                   │
   │ - diagnosis_history                            │
   │ - weather_alerts                               │
   └────────────────────────────────────────────────┘
       ↓
   ┌────────────────────────────────────────────────┐
   │   Telegram API Response                       │
   └────────────┬───────────────────────────────────┘
                ↓
   ┌────────────────────────────────────────────────┐
   │   PETANI (Telegram Reply)                      │
   │   "Tanam PADI minggu depan, harga naik 5%"    │
   └────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Azure Account (Function App, Cosmos DB, AI services)
- Telegram Bot token
- Git

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yourusername/taniwise-bot.git
cd taniwise-bot

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment variables
cp local.settings.json.template local.settings.json
# Edit local.settings.json dengan credentials Azure & Telegram Anda

# 5. Run locally
func start

# 6. Test webhook
curl -X POST http://localhost:7071/api/telegram_webhook \
  -H "Content-Type: application/json" \
  -d '{"message": {"chat": {"id": "123456789"}, "text": "Tanam apa sekarang?"}}'
```

### Deploy to Azure

```bash
# Login to Azure
az login

# Publish function app
az functionapp publish taniwise-bot-dev

# Setup Telegram webhook
# Set webhook URL to: https://taniwise-bot-dev.azurewebsites.net/api/telegram_webhook
```

---

## 📋 Project Structure

```
taniwise-bot/
├── fontte_webhook/
│   ├── function_app.py          # Main webhook handler
│   └── function_app.json
├── shared/
│   ├── __init__.py
│   ├── ai_vision.py             # Plant diagnosis (Custom Vision + GPT-4o)
│   ├── cosmos_db.py             # Database operations
│   ├── recommendation_engine.py  # Recommendation logic (GPT-4o)
│   └── weather_service.py        # Weather data integration
├── requirements.txt              # Python dependencies
├── local.settings.json.template  # Environment template
├── host.json                     # Azure Functions config
├── README.md
└── docs/
    ├── SETUP_CHECKLIST.md       # Step-by-step setup guide
    ├── FONNTE_AZURE_INTEGRATION_GUIDE.md
    └── API_REFERENCE.md
```

---

## 🔑 Environment Variables

Required variables (set in `local.settings.json` or Azure Portal):

```json
{
  "COSMOS_CONNECTION_STRING": "DefaultEndpointProtocol=...",
  "COSMOS_DATABASE_ID": "taniwise-prod",
  "OPENAI_API_KEY": "sk-...",
  "OPENAI_ENDPOINT": "https://xxx.openai.azure.com/",
  "OPENAI_MODEL": "gpt-4",
  "TELEGRAM_BOT_TOKEN": "...",
  "AZURE_VISION_KEY": "...",
  "AZURE_VISION_ENDPOINT": "https://xxx.api.cognitive.microsoft.com/",
  "OPENWEATHERMAP_API_KEY": "...",
  "PIHPS_API_KEY": "..." (optional)
}
```

---

## 📊 API Endpoints

### Webhook Handler
```
POST /api/telegram_webhook

Payload:
{
  "message": {
    "chat": {"id": "123456789"},
    "text": "Tanam apa sekarang?"
  }
}

Response:
{
  "status": "success",
  "message": "Webhook processed",
  "phone": "6281234567890"
}
```

### Health Check
```
GET /api/health

Response:
{
  "status": "healthy",
  "timestamp": "2024-04-21T10:30:00Z",
  "version": "1.0"
}
```

---

## 🧪 Testing

### Local Testing

```bash
# Start local function
func start

# Test text message
curl -X POST http://localhost:7071/api/telegram_webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "chat": {"id": "123456789"},
      "text": "Tanam apa sekarang?"
    }
  }'

# Test image diagnosis
curl -X POST http://localhost:7071/api/telegram_webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "chat": {"id": "123456789"},
      "photo": [
        {"file_id": "ABC123", "file_size": 12345}
      ]
    }
  }'

# Test location
curl -X POST http://localhost:7071/api/telegram_webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "chat": {"id": "123456789"},
      "location": {"latitude": -6.1234, "longitude": 106.5678}
    }
  }'
```

### Azure Logs

```bash
# View live logs
az functionapp log tail --name taniwise-bot-dev --resource-group taniwise-rg

# Or check Application Insights
# Azure Portal → Function App → Application Insights → Logs
```

---

## 📱 WhatsApp Bot Interaction Examples

### Example 1: Text Recommendation
```
User: "Tanam apa sekarang?"

Bot: 🌾 REKOMENDASI TANAM
Berdasarkan cuaca dan harga pasar hari ini:

✅ PADI - Pilihan Terbaik
   • Cuaca: Stabil 90 hari ke depan
   • Harga: Rp3.500/kg (naik 5%)
   • Waktu tanam: Mulai minggu depan
   • Estimasi hasil: Normal, risiko rendah

⚠️ CABAI MERAH - Hindar sekarang
   • Harga: Turun 10% (jangan tanam)
```

### Example 2: Image Diagnosis
```
User: [Sends photo of sick plant]

Bot: 🔍 ANALISIS FOTO TANAMAN
Kondisi: Busuk Patogen
Keyakinan: 92%

Nutrisi: Deficit Kalium

💡 Rekomendasi:
Potong 5cm area busuk, semprotkan fungisida Benomyl.
```

### Example 3: Weather Alert
```
Bot (Proactive): ⚠️ ALERT CUACA EKSTREM
Hujan lebat diprediksi Jum'at jam 2-5 sore.
Amankan panen cabai Anda sekarang!
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Webhook tidak terima message | ✓ Check webhook URL di Telegram Bot settings ✓ Verify Function App running |
| "403 Unauthorized" | ✓ Check API keys di local.settings.json ✓ Verify Azure credentials |
| Diagnosis timeout | ✓ Check image URL accessible ✓ Optimize GPT-4o prompt |
| Cosmos DB error | ✓ Verify connection string format ✓ Check database/collection created |
| Telegram reply tidak terkirim | ✓ Check TELEGRAM_BOT_TOKEN valid |

Lihat [SETUP_CHECKLIST.md](docs/SETUP_CHECKLIST.md) untuk troubleshooting detail.

---

## 📈 Performance Metrics

Target untuk MVP:

| Metric | Target | Current |
|--------|--------|---------|
| Response time | < 3 detik | TBD |
| Diagnosis accuracy | 85%+ | TBD |
| Recommendation adoption rate | 40%+ | TBD |
| Active users (month 1) | 500+ | TBD |
| Uptime | 99.5%+ | TBD |

---

MVP Build Plan
Hour 0-1: Foundation Setup

REQ-1 — Set up Azure Functions project with WhatsApp webhook endpoint and Cosmos DB

    Create Azure Function App (Python/Node.js)
    Set up local development environment
    Create Cosmos DB database for farmer profiles
    Generate WhatsApp webhook URL (you'll use this to register with Meta)

Time estimate: 45 min
Deliverable: Working Azure Function that can receive webhook calls
Hour 1-3: Message Intake

REQ-2 — Implement WhatsApp message receiver (parse text + image messages)

    Implement webhook handler to receive WhatsApp messages
    Parse incoming JSON (text vs. image detection)
    Validate webhook signature from Meta
    Log messages to Cosmos DB

Time estimate: 90 min
Deliverable: Function that receives and logs farmer messages
Hour 3-6: AI Integrations (Parallel Work)

Work on these in parallel if you have multiple team members, or sequentially if solo:

REQ-3 — Integrate GPT-4o for text-based farming advice

    Add Azure OpenAI SDK
    Create system prompt for farming advisor
    Handle text message routing to GPT-4o
    Format response back to WhatsApp

REQ-4 — Integrate computer vision for crop disease detection

    Add Azure Computer Vision API
    Download image from WhatsApp media URL
    Analyze image for crop diseases
    Format diagnosis + recommendations

REQ-5 — Integrate OpenWeatherMap API for weather insights

    Add OpenWeatherMap API key
    Create function to fetch weather by farmer location
    Format weather data for WhatsApp response

REQ-6 — Integrate market price data (PIHPS/BPS)

    Research PIHPS/BPS API endpoints
    Create function to fetch current market prices
    Format price trends for WhatsApp response

Time estimate: 180 min (can be parallelized)
Deliverable: Each AI service responds independently
Hour 6-7: Message Routing Logic

REQ-7 — Implement message routing logic (text → GPT-4o, image → vision, add weather + market data)

    Create router function that decides: is this text or image?
    If text: call GPT-4o + add weather + market data
    If image: call Computer Vision + add recommendations
    Combine all responses into single WhatsApp message
    Send response back via WhatsApp API

Time estimate: 60 min
Deliverable: End-to-end message handling
Hour 7-8: Personalization & Testing

REQ-8 — Store farmer profiles and interaction history in Cosmos DB for personalization

    Create farmer profile schema (location, crop type, farm size)
    Store interaction history with outcomes
    Retrieve farmer context when processing new messages
    Use context to personalize recommendations

REQ-9 (Bonus) — Test end-to-end

    Send test text messages via WhatsApp
    Send test crop images
    Verify responses come back correctly
    Debug any issues

---



## 📄 License

MIT License — See LICENSE file

---



## 📞 Support



## 🚀 Get Started

⭐ Star this repo if you find it helpful!

```bash
# Clone and setup
git clone https://github.com/yourusername/taniwise-bot.git
cd taniwise-bot
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Configure
cp local.settings.json.template local.settings.json
# Edit local.settings.json

# Run
func start

# Deploy
az functionapp publish taniwise-bot-dev
```

**Next:** Read [SETUP_CHECKLIST.md](docs/SETUP_CHECKLIST.md) untuk detail setup step-by-step.

---

**Status:** 🔄 In Development (MVP Phase)  
**Last Updated:** 2024-04-21  
**Version:** 1.0-beta
