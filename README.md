#  AgiChat Bot - AI Assistant untuk Petani Indonesia

**AgiChat** adalah asisten keputusan berbasis **Telegram** untuk petani kecil Indonesia. Memberikan rekomendasi tanam & diagnosis tanaman berdasarkan cuaca lokal, harga pasar, dan analisis gambar - **sepenuhnya offline & gratis** menggunakan AI lokal.

##  Features

| Fitur | Deskripsi | Tech |
|-------|-----------|------|
|  **Text Chat** | Tanya "Tanam apa sekarang?" → Rekomendasi langsung | Mistral 7B (llama.cpp) |
|  **Weather Context** | Cuaca real-time diintegrasikan ke rekomendasi | OpenWeatherMap API |
|  **Price Tracking** | Tren harga pasar per komoditas | PIHPS API |
|  **RAG Retrieval** | Knowledge base pertanian lokal (FAISS) | Sentence-Transformers |
|  **Multi-Model Support** | Fallback ke Ollama jika diperlukan | llama.cpp + Ollama |
|  **Fast Inference** | Respons <5 detik, 100% lokal | LM Studio / llama.cpp |

---

##  Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PETANI (Telegram User)                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓ Telegram Bot Webhook
┌─────────────────────────────────────────────────────────────┐
│               AZURE FUNCTIONS (Serverless)                   │
│         telegram_webhook - Main Handler                      │
└──────┬────────────────────────────────────────────────────┬──┘
       ↓                                                      ↓
   ┌──────────────────┐                         ┌────────────────────┐
   │ AI Response      │                         │ Data Integration   │
   │ (llama.cpp       │                         │ • Weather API      │
   │  + RAG)          │                         │ • Price API        │
   └──────────────────┘                         └────────────────────┘
       ↓
   ┌──────────────────────────────────────────────────────────┐
   │   LOCAL INFERENCE (100% Offline Capable)                 │
   │ - Mistral 7B (1.5GB) via llama.cpp                      │
   │ - FAISS Index (Knowledge Base)                          │
   │ - Fallback: Ollama/LocalAI                              │
   └──────────────────────────────────────────────────────────┘
       ↓
   ┌──────────────────────────────────────────────────────────┐
   │   PETANI (Telegram Response in 2-5 seconds)              │
   │   "Tanam PADI minggu depan, harga naik 5%, cuaca OK"   │
   └──────────────────────────────────────────────────────────┘
```

---

##  Quick Start (5 Minutes)

See [QUICK_START_LLAMA.md](QUICK_START_LLAMA.md) for detailed setup.

```bash
# 1. Setup environment
python -m venv venv
venv\Scripts\activate  # Windows
# or source venv/bin/activate  # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download model (Mistral 7B, ~1.5GB)
mkdir models
huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.1-GGUF ^
  mistral-7b-instruct-v0.1.Q4_K_M.gguf ^
  --local-dir models --local-dir-use-symlinks False

# 4. Configure local.settings.json
cp local.settings.json.template local.settings.json
# Edit: Set LLAMACPP_MODEL_PATH to your model location

# 5. Start bot
func start
# Or: python telegram_webhook/function_app.py
```

**That's it!** Bot responds to Telegram in 2-5 seconds. 🚀


##  Environment Variables

**Minimal setup** (`local.settings.json`):

```json
{
  "AzureWebJobsStorage": "UseDevelopmentStorage=true",
  "FUNCTIONS_WORKER_RUNTIME": "python",
  
  "AI_ENGINE": "llamacpp",
  "LLAMACPP_MODEL_PATH": "C:\\project\\agrichat\\models\\mistral-7b-instruct-v0.1.Q4_K_M.gguf",
  "LLAMACPP_N_CTX": "512",
  "LLAMACPP_N_THREADS": "4",
  "LLAMACPP_N_GPU_LAYERS": "0",
  
  "TELEGRAM_BOT_TOKEN": "YOUR_TOKEN_HERE",
  "OPENWEATHERMAP_API_KEY": "YOUR_API_KEY",
  
  "RAG_TOP_K": "3",
  "RAG_EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2"
}
```

**For Ollama fallback**:
```json
"OLLAMA_URL": "http://localhost:11434",
"OLLAMA_MODEL": "mistral:latest"
```

---

##  Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **AI Model** | Mistral 7B (llama.cpp) | Fast, accurate, offline |
| **Bot Framework** | Telegram Bot API | ~500M daily active users |
| **Knowledge Base** | FAISS + Sentence-Transformers | Real-time RAG retrieval |
| **Inference** | llama.cpp (C++) | <5s response time |
| **Fallback** | Ollama / LocalAI | Flexible deployment |
| **Cloud** | Azure Functions | Serverless (optional) |

---
##  Documentation

- **[QUICK_START_LLAMA.md](QUICK_START_LLAMA.md)** — 5-minute setup guide
- **[local.settings.json.template](local.settings.json.template)** — Environment reference

---

##  Contributing

To improve recommendations:
1. Add training data to `docs/` folder
2. Run `python shared/build_faiss_index.py --src docs`
3. Test with `func start`

---

## Support

Questions? Open an issue or check the [QUICK_START_LLAMA.md](QUICK_START_LLAMA.md) guide.
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



 Star this repo if you find it helpful!

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
