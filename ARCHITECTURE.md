# AgriChat Architecture Diagram

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────┐ │
│  │   WhatsApp      │  │   OpenAI         │  │  OpenWeatherMap    │ │
│  │   Business API  │  │   GPT-4o + Vision│  │   Weather API      │ │
│  └────────┬────────┘  └─────────┬────────┘  └────────┬───────────┘ │
│           │                     │                    │              │
└───────────┼─────────────────────┼────────────────────┼──────────────┘
            │                     │                    │
            │                     │                    │
        ┌───▼──────────────────────▼────────────────────▼────────┐
        │      AZURE FUNCTIONS (Serverless Backend)              │
        ├───────────────────────────────────────────────────────┤
        │                                                        │
        │  ┌──────────────────────────────────────────────────┐ │
        │  │  function_app.py                                 │ │
        │  │  - HTTP Trigger: /api/webhook (GET/POST)        │ │
        │  │  - HTTP Trigger: /api/health (GET)              │ │
        │  └──────────────────────────────────────────────────┘ │
        │                        │                              │
        │  ┌─────────────────────▼──────────────────────────┐  │
        │  │  whatsapp_webhook.py                          │  │
        │  │  - Handles incoming messages                  │  │
        │  │  - Webhook verification                       │  │
        │  │  - Signature validation                       │  │
        │  └─────────────────────┬──────────────────────────┘  │
        │                        │                              │
        │  ┌─────────────────────▼──────────────────────────┐  │
        │  │  message_handler.py                           │  │
        │  │  - Routes message by type (text/image)        │  │
        │  │  - Extracts context from history             │  │
        │  │  - Manages conversation flow                 │  │
        │  └──────┬──────────────────────────┬─────────────┘  │
        │         │                          │                 │
        │  ┌──────▼─────────┐  ┌─────────────▼──────────────┐ │
        │  │ TEXT MESSAGE   │  │ IMAGE MESSAGE              │ │
        │  ├────────────────┤  ├────────────────────────────┤ │
        │  │ openai_        │  │ openai_                    │ │
        │  │ handler.py     │  │ handler.py                 │ │
        │  │ (GPT-4o)       │  │ (Vision API)               │ │
        │  └────────┬───────┘  └──────────┬─────────────────┘ │
        │           │                     │                    │
        │  ┌────────▼─────────────────────▼──────────────────┐ │
        │  │ weather_handler.py                              │ │
        │  │ - Fetch weather data                           │ │
        │  │ - Forecast generation                          │ │
        │  │ - Farming suitability analysis                │ │
        │  └──────────────────┬─────────────────────────────┘ │
        │                     │                                │
        │  ┌──────────────────▼─────────────────────────────┐ │
        │  │ whatsapp_sender.py                            │ │
        │  │ - Format response                             │ │
        │  │ - Send message back                           │ │
        │  └──────────────────┬─────────────────────────────┘ │
        │                     │                                │
        │  ┌──────────────────▼─────────────────────────────┐ │
        │  │ cosmos_handler.py                             │ │
        │  │ - Store interaction in DB                     │ │
        │  │ - Retrieve farmer history                     │ │
        │  │ - Build farmer profile                        │ │
        │  └──────────────────┬─────────────────────────────┘ │
        │                     │                                │
        └─────────────────────┼────────────────────────────────┘
                              │
        ┌─────────────────────▼────────────────────────────────┐
        │  AZURE COSMOS DB (NoSQL Database)                    │
        ├────────────────────────────────────────────────────┤
        │                                                     │
        │  Database: agrichat                                │
        │  Container: interactions (Partition Key: phone#)   │
        │                                                     │
        │  Document Schema:                                  │
        │  {                                                 │
        │    "id": "phone_timestamp",                       │
        │    "phone_number": "919876543210",               │
        │    "user_message": "...",                        │
        │    "assistant_response": "...",                  │
        │    "message_type": "text|image",                 │
        │    "timestamp": "ISO8601",                       │
        │    "metadata": {...}                             │
        │  }                                                │
        │                                                     │
        └─────────────────────────────────────────────────────┘
```

## Message Flow Diagram

### Text Message Flow

```
┌────────────────────────────────────────────────────────────┐
│ FARMER SENDS TEXT MESSAGE VIA WHATSAPP                     │
└────────────┬─────────────────────────────────────────────┘
             │
             ▼
    ┌─────────────────────┐
    │ WhatsApp webhook    │
    │ receives message    │
    └────────┬────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ whatsapp_webhook.py                 │
    │ - Verify token                      │
    │ - Validate signature                │
    │ - Extract phone_number & message    │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ message_handler.py                  │
    │ - Check message type: TEXT          │
    │ - Get farmer history from DB        │
    │ - Call handle_text_message()        │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ Get Context:                        │
    │ ├─ Farmer's past messages           │
    │ ├─ Crop type (from history)         │
    │ └─ Location (from history)          │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ weather_handler.py                  │
    │ - Fetch weather for location        │
    │ - Get 7-day forecast                │
    │ - Analyze farming conditions        │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ openai_handler.py                   │
    │ - Build prompt with context         │
    │ - Include weather data              │
    │ - Include farmer history            │
    │ - Call GPT-4o API                   │
    │ - Get personalized advice           │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ Format response:                    │
    │ - Clear, actionable advice          │
    │ - Emoji for visual appeal           │
    │ - Grouped by topic                  │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ cosmos_handler.py                   │
    │ - Save interaction to DB            │
    │ - phone_number, message, response   │
    │ - timestamp, metadata               │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ whatsapp_sender.py                  │
    │ - Format message for WhatsApp       │
    │ - Split if too long                 │
    │ - Send via WhatsApp Business API    │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ FARMER RECEIVES RESPONSE            │
    │ in WhatsApp within 3-5 seconds      │
    └─────────────────────────────────────┘
```

### Image Message Flow

```
┌────────────────────────────────────────────────────────────┐
│ FARMER SENDS CROP IMAGE VIA WHATSAPP                       │
└────────────┬─────────────────────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ whatsapp_webhook.py                 │
    │ - Extract image_id from message     │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ message_handler.py                  │
    │ - Check message type: IMAGE         │
    │ - Call handle_image_message()       │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ Download image from WhatsApp        │
    │ - Use image_id                      │
    │ - Get signed URL                    │
    │ - Download and convert to base64    │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ openai_handler.py                   │
    │ - Use GPT-4o Vision API             │
    │ - Analyze crop health               │
    │ - Detect diseases                   │
    │ - Assess overall status             │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ Generate Analysis Report:           │
    │ ├─ **Crop Status**: Healthy/At Risk │
    │ ├─ **Issues**: Disease names        │
    │ ├─ **Actions**: What to do now      │
    │ ├─ **Treatment**: Options           │
    │ └─ **Prevention**: Future steps     │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ cosmos_handler.py                   │
    │ - Save interaction & image ref      │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ whatsapp_sender.py                  │
    │ - Send disease analysis report      │
    │ - Add treatment recommendations     │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ FARMER RECEIVES CROP ANALYSIS       │
    │ in WhatsApp within 5-8 seconds      │
    └─────────────────────────────────────┘
```

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     INPUT SOURCES                            │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │  Farmer Text│  │ Farmer Image │  │ External: Weather  │ │
│  │  "How to..."│  │  Crop Photo  │  │ Location, Forecast │
│  └──────┬──────┘  └──────┬───────┘  └────────┬───────────┘ │
│         │                │                   │              │
└─────────┼────────────────┼───────────────────┼──────────────┘
          │                │                   │
          ▼                ▼                   ▼
    ┌──────────────────────────────────────────────────────┐
    │           PROCESSING LAYER (Azure Functions)         │
    ├──────────────────────────────────────────────────────┤
    │                                                       │
    │  ┌─ Text Processing:                                 │
    │  │  └─ GPT-4o → Farming Advice                      │
    │  │                                                   │
    │  ├─ Image Processing:                               │
    │  │  └─ Vision API → Disease Detection               │
    │  │                                                   │
    │  └─ Context Enrichment:                             │
    │     ├─ Farmer History (from DB)                     │
    │     └─ Weather Data (from API)                      │
    │                                                       │
    └──────────────┬───────────────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────────────────┐
    │        PERSISTENCE LAYER (Cosmos DB)                │
    ├──────────────────────────────────────────────────────┤
    │                                                       │
    │  Input Documents:                                    │
    │  ├─ User Message (text/image ID)                   │
    │  ├─ Assistant Response                             │
    │  ├─ Timestamp                                       │
    │  └─ Metadata (location, crop, etc.)               │
    │                                                       │
    │  Queried For:                                        │
    │  ├─ Farmer History (recent 10 interactions)        │
    │  ├─ Farmer Profile (crops, topics)                 │
    │  └─ Interaction Stats                              │
    │                                                       │
    └──────────────┬───────────────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────────────────┐
    │           OUTPUT LAYER (WhatsApp)                    │
    ├──────────────────────────────────────────────────────┤
    │                                                       │
    │  ┌─ Text Response:                                   │
    │  │  └─ Formatted farming advice                     │
    │  │                                                   │
    │  └─ Image Analysis:                                 │
    │     └─ Structured report with recommendations      │
    │                                                       │
    │  Delivery:                                           │
    │  └─ Via WhatsApp Business API                       │
    │                                                       │
    └─────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   AZURE CLOUD                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Azure Functions (Consumption Plan - Serverless)     │  │
│  │                                                      │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │ Function App: agrichat-functions             │   │  │
│  │  │ Runtime: Python 3.11                         │   │  │
│  │  │ Memory: Auto-scale (per request)             │   │  │
│  │  │ Triggers:                                     │   │  │
│  │  │  ├─ /api/webhook (HTTP)                      │   │  │
│  │  │  └─ /api/health (HTTP)                       │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  │                     │                               │  │
│  └─────────────────────┼───────────────────────────────┘  │
│                        │                                   │
│  ┌─────────────────────▼───────────────────────────────┐  │
│  │ Azure Cosmos DB (NoSQL)                            │  │
│  │                                                     │  │
│  │  Database: agrichat                                │  │
│  │  Container: interactions                           │  │
│  │  Partition Key: /phone_number                      │  │
│  │  Throughput: 400 RU/s                              │  │
│  │  Pricing: Free Tier / Pay-as-you-go                │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Azure Storage Account                               │  │
│  │ (For function deployment packages)                  │  │
│  │                                                      │  │
│  │  Container: function packages                       │  │
│  │  Tables: Logging & telemetry                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Application Insights (Optional)                      │  │
│  │ - Performance monitoring                            │  │
│  │ - Error tracking                                    │  │
│  │ - Custom metrics                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│ SECURITY LAYERS                                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 1. INPUT VALIDATION                                     │
│    ├─ Webhook signature verification (HMAC-SHA256)      │
│    ├─ Phone number format validation                    │
│    ├─ Message payload schema validation                 │
│    └─ Rate limiting (optional)                          │
│                                                          │
│ 2. CREDENTIALS MANAGEMENT                               │
│    ├─ Environment variables (not hardcoded)             │
│    ├─ Azure Key Vault (recommended for production)      │
│    ├─ .env file (git ignored)                           │
│    └─ local.settings.json (git ignored)                 │
│                                                          │
│ 3. API AUTHENTICATION                                   │
│    ├─ OpenAI: API Key in headers                        │
│    ├─ WhatsApp: OAuth tokens & app secrets              │
│    ├─ OpenWeatherMap: API key query param               │
│    └─ Cosmos DB: Connection string (encrypted)          │
│                                                          │
│ 4. DATA PROTECTION                                      │
│    ├─ HTTPS/TLS for all external calls                  │
│    ├─ Cosmos DB: Encryption at rest                     │
│    ├─ Cosmos DB: Role-based access control              │
│    └─ No sensitive data in logs                         │
│                                                          │
│ 5. ERROR HANDLING                                       │
│    ├─ Try-catch blocks in all handlers                  │
│    ├─ No stack traces exposed to users                  │
│    ├─ Error logging without sensitive info              │
│    └─ Graceful degradation                              │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

**Architecture Last Updated**: April 27, 2026  
**Version**: 1.0.0 MVP
