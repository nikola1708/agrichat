"""
Azure Function handler for Fonnte WhatsApp webhooks
Main entry point for TaniWise Bot
"""
import azure.functions as func
import json
import logging
import os
import requests
from datetime import datetime

# Import shared modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.cosmos_db import CosmosDBManager
from shared.ai_vision import PlantDiagnosisEngine
from shared.recommendation_engine import RecommendationEngine
from shared.weather_service import WeatherService
from shared.price_service import PriceService
from shared.fonnte_api import FontneAPIClient

# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize services
cosmos_db = CosmosDBManager()
plant_engine = PlantDiagnosisEngine()
recommendation_engine = RecommendationEngine()
weather_service = WeatherService()
price_service = PriceService()
fonnte_client = FontneAPIClient()


async def handle_text_message(phone: str, message: str) -> str:
    """
    Handle incoming text messages
    Route to appropriate handler based on content
    """
    try:
        logger.info(f"Processing text message from {phone}: {message[:50]}...")

        # Get farmer profile for personalization
        farmer_profile = cosmos_db.get_farmer_profile(phone)
        
        # Get weather data (default Jakarta if no location in profile)
        latitude = farmer_profile.get("latitude", -6.2088) if farmer_profile else -6.2088
        longitude = farmer_profile.get("longitude", 106.8456) if farmer_profile else 106.8456
        
        weather_data = weather_service.get_current_weather(latitude, longitude)
        
        # Get price data
        price_data = price_service.get_commodity_prices()

        # Generate recommendation using GPT-4o
        recommendation = recommendation_engine.get_recommendation(
            query=message,
            weather_data=weather_data,
            price_data=price_data,
            farmer_context=farmer_profile
        )

        # Format response
        response = recommendation_engine.format_recommendation_response(recommendation)
        
        # Add weather info if available
        if weather_data:
            weather_msg = weather_service.format_weather_message(weather_data)
            response = f"{response}\n\n{weather_msg}"

        # Add price analysis
        price_msg = price_service.get_price_recommendation(["padi", "jagung", "cabai_merah"])
        response = f"{response}\n\n{price_msg}"

        # Save to history
        history_entry = {
            "type": "text",
            "message": message,
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        }
        cosmos_db.save_diagnosis_history(phone, history_entry)

        return response

    except Exception as e:
        logger.error(f"Error handling text message: {str(e)}")
        return f"❌ Maaf, ada error saat memproses pertanyaan Anda: {str(e)}"


async def handle_image_message(phone: str, media_url: str) -> str:
    """
    Handle incoming image messages
    Perform plant disease diagnosis
    """
    try:
        logger.info(f"Processing image message from {phone}: {media_url}")

        # Diagnose plant disease
        diagnosis = plant_engine.analyze_plant_image(media_url)

        # Format response
        response = plant_engine.format_diagnosis_response(diagnosis)

        # Save to history
        history_entry = {
            "type": "image",
            "media_url": media_url,
            "diagnosis": diagnosis,
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        }
        cosmos_db.save_diagnosis_history(phone, history_entry)

        return response

    except Exception as e:
        logger.error(f"Error handling image message: {str(e)}")
        return f"❌ Error: Tidak bisa menganalisis foto. Silakan kirim foto yang lebih jelas."


async def handle_location_message(phone: str, latitude: float, longitude: float) -> str:
    """
    Handle location messages
    Save location to farmer profile and send location-specific recommendations
    """
    try:
        logger.info(f"Processing location from {phone}: ({latitude}, {longitude})")

        # Update farmer profile with location
        farmer_profile = cosmos_db.get_farmer_profile(phone) or {"id": phone, "phone": phone}
        farmer_profile["latitude"] = latitude
        farmer_profile["longitude"] = longitude
        farmer_profile["last_location_update"] = datetime.utcnow().isoformat()
        
        cosmos_db.save_farmer_profile(phone, farmer_profile)

        # Get location-specific weather
        weather_data = weather_service.get_current_weather(latitude, longitude)
        forecast_data = weather_service.get_forecast(latitude, longitude)

        response = "✅ Lokasi tersimpan!\n\n"
        
        # Check for extreme weather
        if weather_data:
            extreme_warning = weather_service.detect_extreme_weather(weather_data)
            if extreme_warning:
                response += f"{extreme_warning}\n\n"
            
            response += weather_service.format_weather_message(weather_data)

        # Add forecast info
        if forecast_data:
            response += "\n\n📅 PRAKIRAAN CUACA 5 HARI:\n"
            for i, forecast in enumerate(forecast_data.get("forecasts", [])[:8:2]):  # Show every 6 hours
                response += f"   • {forecast['description'].capitalize()}\n"

        return response

    except Exception as e:
        logger.error(f"Error handling location message: {str(e)}")
        return f"❌ Error: Tidak bisa memproses lokasi Anda."


async def main_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main webhook handler for all Fonnte messages
    """
    try:
        # Parse request
        req_json = req.get_json()
        logger.info(f"Received webhook: {json.dumps(req_json, default=str)}")

        # Validate payload
        if not FontneAPIClient.validate_webhook_payload(req_json):
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "Invalid payload"}),
                status_code=400,
                mimetype="application/json"
            )

        phone = req_json.get("sender")
        message_type = req_json.get("type")
        
        logger.info(f"Processing {message_type} message from {phone}")

        # Route based on message type
        response_text = None

        if message_type == "text":
            response_text = await handle_text_message(phone, req_json.get("message", ""))

        elif message_type == "image":
            response_text = await handle_image_message(phone, req_json.get("media_url", ""))

        elif message_type == "location":
            response_text = await handle_location_message(
                phone,
                req_json.get("latitude"),
                req_json.get("longitude")
            )

        # Send response back via Fonnte
        if response_text:
            success = fonnte_client.send_text_message(phone, response_text)
            
            if not success:
                logger.error(f"Failed to send response to {phone}")

        # Return success response
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "message": "Webhook processed",
                "phone": phone
            }),
            status_code=200,
            mimetype="application/json"
        )

    except ValueError:
        logger.error("Invalid JSON in request")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Unexpected error in webhook handler: {str(e)}")
        return func.HttpResponse(
            json.dumps({"status": "error", "message": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


# Azure Functions trigger
app = func.FunctionApp()


@app.route(route="fontte_webhook", methods=["POST"])
async def fontte_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger for Fonnte webhook
    
    Webhook URL format:
    https://<function-app-name>.azurewebsites.net/api/fontte_webhook
    """
    return await main_handler(req)


@app.route(route="health", methods=["GET"])
async def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    return func.HttpResponse(
        json.dumps({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0"
        }),
        status_code=200,
        mimetype="application/json"
    )
