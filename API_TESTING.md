# AgriChat API Testing Guide

## Local Testing

### Prerequisites
- Azure Functions running: `func start`
- ngrok tunnel (for WhatsApp webhook): `ngrok http 7071`

## Test Cases

### 1. Health Check Endpoint

```bash
curl http://localhost:7071/api/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-04-27T10:30:00.123456",
  "version": "1.0.0"
}
```

### 2. Webhook Verification (GET)

```bash
curl "http://localhost:7071/api/webhook?hub.verify_token=agrichat_verify_token_dev&hub.challenge=test_challenge_123"
```

**Expected Response**: `test_challenge_123`

### 3. Text Message - Farming Advice

**Simulate WhatsApp webhook POST**:

```bash
curl -X POST http://localhost:7071/api/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "field": "messages",
        "value": {
          "messages": [{
            "from": "919876543210",
            "id": "wamid.123456",
            "timestamp": "1234567890",
            "type": "text",
            "text": {
              "body": "When should I plant rice in Delhi?"
            }
          }],
          "contacts": [{
            "profile": {
              "name": "Rajesh Kumar"
            },
            "wa_id": "919876543210"
          }]
        }
      }]
    }]
  }'
```

**Flow**:
1. Webhook receives text message
2. Routes to `handle_text_message()`
3. Gets farmer history from Cosmos DB
4. Fetches weather for Delhi
5. Calls GPT-4o with context
6. Sends response via WhatsApp

**Expected Logs**:
```
Processing text message from 919876543210
Generated farming advice for 919876543210
Message sent to 919876543210 (ID: wamid.123456)
```

### 4. Image Message - Crop Disease Detection

```bash
curl -X POST http://localhost:7071/api/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "field": "messages",
        "value": {
          "messages": [{
            "from": "919876543210",
            "id": "wamid.789012",
            "timestamp": "1234567891",
            "type": "image",
            "image": {
              "id": "image_123456",
              "mime_type": "image/jpeg"
            }
          }],
          "contacts": [{
            "profile": {
              "name": "Rajesh Kumar"
            },
            "wa_id": "919876543210"
          }]
        }
      }]
    }]
  }'
```

**Flow**:
1. Webhook receives image message
2. Routes to `handle_image_message()`
3. Downloads image from WhatsApp servers
4. Sends to GPT-4o Vision API
5. Analyzes for diseases/health
6. Sends recommendations

**Expected Response**:
```
**Crop Status**: Healthy
**Identified Issues**: None visible
**Immediate Actions**: Continue current practices
**Treatment Options**: None needed at this time
```

### 5. Invalid Verify Token

```bash
curl "http://localhost:7071/api/webhook?hub.verify_token=wrong_token&hub.challenge=test123"
```

**Expected Response**: HTTP 403 Forbidden

### 6. Invalid Method

```bash
curl -X DELETE http://localhost:7071/api/webhook
```

**Expected Response**: HTTP 405 Method not allowed

## Integration Testing

### Test Weather Integration

```bash
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
            "text": {
              "body": "Is it good time to plant tomatoes? My location is Mumbai"
            }
          }],
          "contacts": [{
            "wa_id": "919876543210"
          }]
        }
      }]
    }]
  }'
```

**Expected**: Response includes weather-specific advice for Mumbai

### Test Conversation History

Send multiple messages in sequence:

```bash
# Message 1: What crop?
curl -X POST http://localhost:7071/api/webhook \
  -d '{"entry":[{"changes":[{"field":"messages","value":{"messages":[{"from":"919876543210","type":"text","text":{"body":"I have wheat"}}],"contacts":[{"wa_id":"919876543210"}]}}]}]}'

# Message 2: Should reference wheat from previous message
curl -X POST http://localhost:7071/api/webhook \
  -d '{"entry":[{"changes":[{"field":"messages","value":{"messages":[{"from":"919876543210","type":"text","text":{"body":"How much fertilizer?"}}],"contacts":[{"wa_id":"919876543210"}]}}]}]}'
```

**Expected**: Second response should reference wheat crop

## WhatsApp Sandbox Testing

### Setup Sandbox Number

1. Go to Meta App Dashboard → WhatsApp → Sandbox
2. Scan QR code
3. Send message to test number (e.g., +1 555-123-4567)

### Send Test Messages

**Text Message**:
```
Hi, when should I plant rice?
```

**Expected**: Receives farming advice within 3 seconds

**Image Message**:
- Take photo of any plant
- Send via WhatsApp
- Expect crop analysis

## Performance Testing

### Load Test (Simulated)

```bash
# Send 10 messages in sequence
for i in {1..10}; do
  curl -X POST http://localhost:7071/api/webhook \
    -H "Content-Type: application/json" \
    -d "{\"entry\":[{\"changes\":[{\"field\":\"messages\",\"value\":{\"messages\":[{\"from\":\"919876543210\",\"type\":\"text\",\"text\":{\"body\":\"Test message $i\"}}],\"contacts\":[{\"wa_id\":\"919876543210\"}]}}]}]}" \
    &
done
wait
```

**Metrics**:
- Response time: < 2 seconds
- Success rate: 100%
- Concurrent requests: Should handle 10+

## Error Handling Tests

### Test: Missing Phone Number

```bash
curl -X POST http://localhost:7071/api/webhook \
  -d '{"entry":[{"changes":[{"field":"messages","value":{"messages":[{"type":"text","text":{"body":"test"}}],"contacts":[]}}]}]}'
```

**Expected**: Graceful error handling, logged error

### Test: Invalid JSON

```bash
curl -X POST http://localhost:7071/api/webhook \
  -H "Content-Type: application/json" \
  -d 'invalid json'
```

**Expected**: HTTP 500 with error message

### Test: Missing Message Body

```bash
curl -X POST http://localhost:7071/api/webhook \
  -d '{"entry":[{"changes":[{"field":"messages","value":{"messages":[{"from":"919876543210","type":"text"}],"contacts":[{"wa_id":"919876543210"}]}}]}]}'
```

**Expected**: Handled gracefully, message sent to user asking for clarification

## Database Testing (Cosmos DB)

### Verify Data Storage

```python
# In Python REPL
from functions.cosmos_handler import get_farmer_history, get_farmer_profile

history = get_farmer_history("919876543210", limit=5)
print(f"Interactions: {len(history)}")

profile = get_farmer_profile("919876543210")
print(f"Topics: {profile['topics']}")
print(f"Crops: {profile['crops']}")
```

### Check Cosmos DB Portal

1. Azure Portal → Your Cosmos DB Account
2. Data Explorer
3. Select database "agrichat" → container "interactions"
4. View documents by phone number

## Logging & Debugging

### Enable Debug Logging

Update `function_app.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

### View Logs Locally

```bash
# Terminal where func start is running
# Look for INFO, WARNING, ERROR messages
```

### Azure Logs

```bash
az functionapp log tail --name agrichat-functions --resource-group agrichat-rg
```

## API Response Time Benchmarks

| Operation | Target Time | Notes |
|-----------|------------|-------|
| Webhook verification | < 100ms | Should be immediate |
| Text message processing | < 3 seconds | Includes API calls |
| Image analysis | < 5 seconds | Vision API can be slower |
| Database save | < 500ms | Cosmos DB latency |
| Weather fetch | < 2 seconds | API dependent |
| GPT-4o response | < 2 seconds | Token count dependent |

## Success Criteria

- [ ] All health checks pass
- [ ] Webhook verification works
- [ ] Text messages processed correctly
- [ ] Image analysis works
- [ ] Responses sent back via WhatsApp
- [ ] Data stored in database
- [ ] Error handling graceful
- [ ] Logs informative
- [ ] Performance acceptable

## Troubleshooting Test Failures

### Message not received
1. Check webhook logs for errors
2. Verify message format is correct
3. Check phone number format (with country code)
4. Verify WhatsApp Business account

### Slow responses
1. Check OpenAI API status
2. Check network connectivity
3. Monitor Azure Function duration
4. Check Cosmos DB latency

### API errors
1. Verify all API keys are valid
2. Check rate limits not exceeded
3. Review API service status
4. Check error logs for details
