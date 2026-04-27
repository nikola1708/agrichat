# AgriChat Deployment Checklist

## Pre-Deployment ✅

### Code Quality
- [ ] All Python files syntax validated
- [ ] No hardcoded secrets in code
- [ ] Error handling in all endpoints
- [ ] Logging enabled
- [ ] Dependencies in requirements.txt

### Local Testing
- [ ] Local function app runs without errors
- [ ] Health endpoint responds
- [ ] Webhook verification works
- [ ] Text message handling works
- [ ] Image message handling works
- [ ] API keys working locally

### Credentials Ready
- [ ] OpenAI API key tested
- [ ] OpenWeatherMap API key (if using)
- [ ] WhatsApp Business credentials (if production)
- [ ] Azure Storage connection string
- [ ] Cosmos DB connection string (if using)

## Deployment Steps ✅

### Step 1: Prepare Azure Resources

```bash
# Set project variables
PROJECT_NAME="agrichat"
LOCATION="eastus"
RESOURCE_GROUP="${PROJECT_NAME}-rg"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create storage account
az storage account create \
  --name ${PROJECT_NAME}stg \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

- [ ] Resource group created
- [ ] Storage account created
- [ ] Storage account connection string noted

### Step 2: Create Function App

```bash
# Create function app
az functionapp create \
  --resource-group $RESOURCE_GROUP \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name ${PROJECT_NAME}-functions-$(date +%s) \
  --storage-account ${PROJECT_NAME}stg
```

- [ ] Function app created
- [ ] Function app name noted
- [ ] Runtime version correct (Python 3.11)

### Step 3: Configure Application Settings

```bash
FUNC_APP_NAME="agrichat-functions-xxxxx"

# Set all required settings
az functionapp config appsettings set \
  --name $FUNC_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
  OPENAI_API_KEY="sk-proj-..." \
  WHATSAPP_PHONE_NUMBER_ID="your-id" \
  WHATSAPP_ACCESS_TOKEN="your-token" \
  WHATSAPP_VERIFY_TOKEN="agrichat_verify_prod" \
  OPENWEATHER_API_KEY="your-key" \
  COSMOS_CONNECTION_STRING="your-connection-string" \
  COSMOS_DB_NAME="agrichat" \
  COSMOS_CONTAINER_NAME="interactions"
```

- [ ] All environment variables set
- [ ] Variables verified in Azure portal
- [ ] No placeholder values remaining

### Step 4: Deploy Code

```bash
# From project root
func azure functionapp publish $FUNC_APP_NAME --build remote
```

- [ ] Code deployment successful
- [ ] No build errors
- [ ] All functions listed in output

### Step 5: Verify Deployment

```bash
# Check function app health
curl https://${FUNC_APP_NAME}.azurewebsites.net/api/health

# Check logs
az functionapp log tail --name $FUNC_APP_NAME --resource-group $RESOURCE_GROUP
```

- [ ] Health endpoint returns 200
- [ ] No errors in logs
- [ ] Function app is running

## WhatsApp Configuration ✅

### Webhook Setup

- [ ] Callback URL updated to: `https://<your-function>.azurewebsites.net/api/webhook`
- [ ] Verify token updated to production value
- [ ] Webhook subscriptions enabled:
  - [ ] messages
  - [ ] message_template_status_update (optional)
  - [ ] message_template_quality_notification (optional)

### Business Account

- [ ] WhatsApp Business account created/updated
- [ ] Phone number verified
- [ ] Business information complete
- [ ] API access confirmed

## Testing (Post-Deployment) ✅

### Smoke Tests

```bash
# Test health endpoint
curl https://<your-function>.azurewebsites.net/api/health

# Test webhook verification
curl "https://<your-function>.azurewebsites.net/api/webhook?hub.verify_token=agrichat_verify_prod&hub.challenge=test123"
```

- [ ] Health check passes
- [ ] Webhook verification returns challenge

### Functional Tests

- [ ] Send test text message via WhatsApp
  - [ ] Message appears in function logs
  - [ ] Response received in WhatsApp within 5 seconds
  
- [ ] Send test image via WhatsApp
  - [ ] Image is analyzed
  - [ ] Disease detection response received
  
- [ ] Check Cosmos DB (if configured)
  - [ ] Interactions stored
  - [ ] Data retrieval works

### Integration Tests

- [ ] GPT-4o API responding
- [ ] Weather API responding
- [ ] WhatsApp API responding
- [ ] All responses include proper formatting

### Performance Tests

- [ ] Response time < 5 seconds (text)
- [ ] Response time < 8 seconds (image)
- [ ] No timeout errors
- [ ] Concurrent messages handled

## Monitoring Setup ✅

### Azure Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app $FUNC_APP_NAME \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP

# Link to Function App
az functionapp config appsettings set \
  --name $FUNC_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY="<key>"
```

- [ ] Application Insights created
- [ ] Linked to Function App
- [ ] Telemetry flowing

### Log Setup

```bash
# View logs
az functionapp log tail --name $FUNC_APP_NAME --resource-group $RESOURCE_GROUP
```

- [ ] Real-time logs working
- [ ] Can see incoming messages
- [ ] Can see errors/warnings

### Alerts (Optional)

- [ ] Alert for function errors
- [ ] Alert for high latency (> 10s)
- [ ] Alert for quota issues
- [ ] Alert for API failures

## Security Audit ✅

### Code Security

- [ ] No hardcoded API keys
- [ ] No debug mode enabled
- [ ] HTTPS enforced
- [ ] Input validation implemented
- [ ] Error messages don't leak sensitive info

### API Security

- [ ] Webhook signature verification enabled
- [ ] Rate limiting considered
- [ ] Phone number format validated
- [ ] Message content validated

### Data Security

- [ ] Cosmos DB encrypted
- [ ] Connection strings use Azure Key Vault (recommended)
- [ ] No sensitive logs exposed
- [ ] Data retention policy set

### Access Control

- [ ] Only needed people have access
- [ ] Service principal used for deployment
- [ ] API keys rotated regularly
- [ ] Audit logging enabled

## Cost Optimization ✅

### Azure Resources

- [ ] Consumption plan selected (pay-per-use)
- [ ] Storage tier optimized
- [ ] Cosmos DB RUs scaled appropriately
- [ ] Auto-scaling enabled

### API Usage

- [ ] OpenWeatherMap free tier sufficient
- [ ] OpenAI costs tracked
- [ ] WhatsApp costs monitored
- [ ] Budget alerts set

## Documentation ✅

- [ ] README.md reviewed
- [ ] SETUP_GUIDE.md reviewed
- [ ] API_TESTING.md reviewed
- [ ] Deployment instructions documented
- [ ] Runbook created for support
- [ ] Incident response plan ready

## Post-Deployment Tasks ✅

### Day 1
- [ ] Monitor logs for errors
- [ ] Test with 5-10 real users
- [ ] Collect initial feedback
- [ ] Check cost estimates

### Week 1
- [ ] Review performance metrics
- [ ] Optimize slow queries
- [ ] Adjust rate limits if needed
- [ ] Document issues encountered

### Month 1
- [ ] Analyze usage patterns
- [ ] Optimize costs
- [ ] Plan feature improvements
- [ ] Update documentation

## Rollback Plan

If issues occur:

```bash
# Revert to previous version
git checkout <previous-commit>
func azure functionapp publish $FUNC_APP_NAME --build remote

# Or, disable function app
az functionapp stop --name $FUNC_APP_NAME --resource-group $RESOURCE_GROUP
```

- [ ] Rollback procedure documented
- [ ] Previous version backed up
- [ ] Team trained on rollback steps

## Sign-off

- [ ] Development Lead: ____________________ Date: ____
- [ ] QA Lead: ____________________ Date: ____
- [ ] DevOps Lead: ____________________ Date: ____
- [ ] Product Manager: ____________________ Date: ____

## Notes

```
[Add any deployment notes, issues, or special considerations here]
```

---

**Deployment Completion Time**: _______________
**Deployed By**: _______________
**Date**: _______________
