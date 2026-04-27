# API Reference - TaniWise Bot

Complete API documentation untuk semua endpoints dan payloads.

---

## Endpoints

### 1. Fontte Webhook (Primary)

**URL:** `POST /api/fontte_webhook`

**Description:** Main webhook endpoint untuk menerima pesan dari Fonnte WhatsApp API

**Request Headers:**
```
Content-Type: application/json
```

**Request Body - Text Message:**
```json
{
  "sender": "628123456789",
  "type": "text",
  "message": "Tanam apa sekarang?"
}
```

**Request Body - Image Message:**
```json
{
  "sender": "628123456789",
  "type": "image",
  "media_url": "https://example.com/plant.jpg"
}
```

**Request Body - Location Message:**
```json
{
  "sender": "628123456789",
  "type": "location",
  "latitude": -6.2088,
  "longitude": 106.8456
}
```

**Success Response:**
```json
{
  "status": "success",
  "message": "Webhook processed",
  "phone": "628123456789"
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Invalid payload"
}
```

---

### 2. Health Check

**URL:** `GET /api/health`

**Description:** Check if function is running

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-04-21T10:30:00Z",
  "version": "1.0"
}
```

---

## Message Processing Flow

### Text Message Flow

```
1. Farmer sends: "Tanam apa sekarang?"
   ↓
2. Fonnte webhook triggers: POST /api/fontte_webhook
   ↓
3. Parse: {sender, type: "text", message}
   ↓
4. Fetch farmer profile (from Cosmos DB)
   ↓
5. Get weather data (OpenWeatherMap)
   ↓
6. Get price data (PriceService)
   ↓
7. Call GPT-4o:
   - Input: question + weather + prices + farmer context
   - Output: Recommendation JSON
   ↓
8. Format response for WhatsApp
   ↓
9. Call Fonnte API: POST /api/send
   {
     "target": "628123456789",
     "message": "🌾 REKOMENDASI TANAM...",
     "device": "device_123"
   }
   ↓
10. Response delivered to WhatsApp
```

---

### Image Message Flow

```
1. Farmer sends: Photo of plant
   ↓
2. Fonnte webhook triggers
   ↓
3. Parse: {sender, type: "image", media_url}
   ↓
4. Download image from media_url
   ↓
5. Validate image format
   ↓
6. Call GPT-4o Vision:
   - Input: image + system prompt
   - Output: Diagnosis JSON
   {
     "plant_name": "Tanaman Padi",
     "health_status": "sakit",
     "disease_name": "Blas Daun",
     "confidence": 92,
     "treatment_recommendation": "..."
   }
   ↓
7. Format diagnosis for WhatsApp
   ↓
8. Send via Fonnte API
   ↓
9. Farmer gets diagnosis + treatment
```

---

### Location Message Flow

```
1. Farmer shares: Location
   ↓
2. Fontte webhook triggers
   ↓
3. Parse: {sender, type: "location", latitude, longitude}
   ↓
4. Update farmer profile in Cosmos DB
   ↓
5. Get weather for location (OpenWeatherMap)
   ↓
6. Get 5-day forecast
   ↓
7. Check for extreme weather alerts
   ↓
8. Format weather + forecast message
   ↓
9. Send via Fonnte API
```

---

## External APIs

### OpenAI (GPT-4o)

**Endpoint:** `https://<resource>.openai.azure.com/openai/deployments/gpt-4/chat/completions`

**Method:** POST

**Headers:**
```
Content-Type: application/json
api-key: <OPENAI_API_KEY>
```

**Request:**
```python
{
  "messages": [
    {
      "role": "system",
      "content": "Anda adalah ahli agronomi Indonesia..."
    },
    {
      "role": "user",
      "content": "Tanam apa sekarang?"
    }
  ],
  "max_tokens": 1500,
  "temperature": 0.7
}
```

---

### OpenWeatherMap API

**Endpoint:** `https://api.openweathermap.org/data/2.5/weather`

**Query Parameters:**
```
lat=<latitude>
lon=<longitude>
appid=<API_KEY>
units=metric
lang=id
```

**Response:**
```json
{
  "main": {
    "temp": 28.5,
    "feels_like": 30.2,
    "humidity": 75,
    "pressure": 1013
  },
  "weather": [
    {
      "main": "Clouds",
      "description": "Awan terputus-putus"
    }
  ],
  "wind": {
    "speed": 3.5
  }
}
```

---

### Fonnte API

**Send Message Endpoint:**
```
POST https://api.fonnte.com/send
```

**Headers:**
```
Authorization: <FONNTE_API_TOKEN>
Content-Type: application/json
```

**Request Body:**
```json
{
  "target": "628123456789",
  "message": "Pesan Anda",
  "device": "device_123"
}
```

**Response:**
```json
{
  "status": 200,
  "response": "success",
  "data": {
    "message_id": "msg_123"
  }
}
```

---

## Cosmos DB Collections

### Collection: petani (Farmer Profiles)

**Partition Key:** `/phone`

**Schema:**
```json
{
  "id": "628123456789",
  "phone": "628123456789",
  "name": "Bapak Sutrisno",
  "location_name": "Karawang, Jawa Barat",
  "latitude": -6.3088,
  "longitude": 107.3259,
  "farm_size_hectares": 0.25,
  "crops": ["padi", "jagung"],
  "experience_years": 5,
  "created_at": "2024-04-21T10:00:00Z",
  "updated_at": "2024-04-21T12:00:00Z",
  "last_location_update": "2024-04-21T12:00:00Z"
}
```

---

### Collection: diagnosis_history

**Partition Key:** `/phone`

**Schema:**
```json
{
  "id": "628123456789_1713688800",
  "phone": "628123456789",
  "type": "image",
  "message": "Tanam apa sekarang?",
  "media_url": "https://...",
  "diagnosis": {
    "plant_name": "Padi",
    "disease_name": "Blas Daun",
    "confidence": 92,
    "treatment": "..."
  },
  "response": "🔍 ANALISIS FOTO...",
  "timestamp": "2024-04-21T12:00:00Z"
}
```

---

### Collection: weather_alerts

**Partition Key:** `/phone`

**Schema:**
```json
{
  "id": "628123456789_1713688800",
  "phone": "628123456789",
  "alert_type": "heavy_rain|extreme_heat|strong_wind",
  "severity": "warning|critical",
  "message": "Hujan lebat diprediksi Jum'at...",
  "timestamp": "2024-04-21T12:00:00Z",
  "location": {
    "latitude": -6.2088,
    "longitude": 106.8456
  }
}
```

---

## Data Types & Formats

### Phone Number Format
- Format: `628123456789`
- Length: 12 digits
- No plus sign
- No spaces or dashes
- Must start with 62 (Indonesia country code)

### Date Format
- ISO 8601: `2024-04-21T10:30:00Z`
- Always UTC timezone
- Include milliseconds when available

### Coordinates (Latitude/Longitude)
- Latitude: -6.2088 (South is negative)
- Longitude: 106.8456 (East is positive)
- Precision: 4 decimal places

---

## Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | Success | Message processed |
| 400 | Bad Request | Check JSON format |
| 403 | Unauthorized | Check API credentials |
| 404 | Not Found | Check endpoint URL |
| 500 | Server Error | Check Azure Function logs |
| 503 | Service Unavailable | External API down |

---

## Rate Limits

| Service | Limit | Period |
|---------|-------|--------|
| Fonnte | 100 requests | Per minute |
| OpenAI | 200 requests | Per minute |
| OpenWeatherMap | 1000 calls | Per day (free) |
| Azure Functions | Unlimited | Consumption plan |

---

## Testing Examples

### cURL - Text Message
```bash
curl -X POST http://localhost:7071/api/fontte_webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "628123456789",
    "type": "text",
    "message": "Tanam apa sekarang?"
  }'
```

### cURL - Image Message
```bash
curl -X POST http://localhost:7071/api/fontte_webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "628123456789",
    "type": "image",
    "media_url": "https://upload.wikimedia.org/wikipedia/commons/..."
  }'
```

### Python - Send Message
```python
import requests

headers = {
    "Authorization": "your-fonnte-token",
    "Content-Type": "application/json"
}

payload = {
    "target": "628123456789",
    "message": "Tanam PADI minggu depan",
    "device": "device_123"
}

response = requests.post(
    "https://api.fonnte.com/send",
    json=payload,
    headers=headers
)
print(response.json())
```

---

**Last Updated:** 2024-04-21  
**Version:** 1.0
