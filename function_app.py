
import azure.functions as func
import json
import logging
import os
from datetime import datetime

# Import shared modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.cosmos_db import CosmosDBManager
from shared.ai_vision import PlantDiagnosisEngine
from shared.recommendation_engine import RecommendationEngine
from shared.weather_service import WeatherService
from shared.price_service import PriceService
from shared.telegram_api import TelegramAPIClient
from shared.ai_engine import get_ai_engine

# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize services
cosmos_db = CosmosDBManager()
plant_engine = PlantDiagnosisEngine()
recommendation_engine = RecommendationEngine()
weather_service = WeatherService()
price_service = PriceService()
telegram_client = TelegramAPIClient()
ai_engine = get_ai_engine()


async def handle_text_message(chat_id: str, message: str) -> str:
    """
    Handle incoming text messages from Telegram by forwarding to the
    configured local AI engine (Ollama / LocalAI) and returning its reply.
    """
    try:
        logger.info(f"Forwarding text message from {chat_id} to AI engine: {message[:80]}...")

        # Generate reply from local AI engine. The engine adapter will
        # include a system prompt and attach the user id to preserve
        # per-user context/hints.
        response = ai_engine.generate_response(chat_id, message)

        # Save minimal history for auditing
        try:
            history_entry = {
                "type": "text",
                "message": message,
                "response": response,
                "timestamp": datetime.utcnow().isoformat()
            }
            cosmos_db.save_diagnosis_history(chat_id, history_entry)
        except Exception:
            logger.debug("Could not save history to CosmosDB; continuing")

        return response

    except Exception as e:
        logger.error(f"Error handling text message: {str(e)}")
        return f"❌ Maaf, ada error saat memproses pertanyaan Anda: {str(e)}"


async def handle_image_message(chat_id: str, media_url: str) -> str:
    """
    Handle incoming image messages from Telegram.
    """
    try:
        logger.info(f"Processing image message from {chat_id}: {media_url}")

        diagnosis = plant_engine.analyze_plant_image(media_url)
        response = plant_engine.format_diagnosis_response(diagnosis)

        history_entry = {
            "type": "image",
            "media_url": media_url,
            "diagnosis": diagnosis,
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        }
        cosmos_db.save_diagnosis_history(chat_id, history_entry)

        return response

    except Exception as e:
        logger.error(f"Error handling image message: {str(e)}")
        return "❌ Error: Tidak bisa menganalisis foto. Silakan kirim foto yang lebih jelas."


async def handle_location_message(chat_id: str, latitude: float, longitude: float) -> str:
    """
    Handle location messages from Telegram.
    """
    try:
        logger.info(f"Processing location from {chat_id}: ({latitude}, {longitude})")

        farmer_profile = cosmos_db.get_farmer_profile(chat_id) or {"id": chat_id, "chat_id": chat_id}
        farmer_profile["latitude"] = latitude
        farmer_profile["longitude"] = longitude
        farmer_profile["last_location_update"] = datetime.utcnow().isoformat()
        cosmos_db.save_farmer_profile(chat_id, farmer_profile)

        weather_data = weather_service.get_current_weather(latitude, longitude)
        forecast_data = weather_service.get_forecast(latitude, longitude)

        response = "✅ Lokasi tersimpan!\n\n"

        if weather_data:
            extreme_warning = weather_service.detect_extreme_weather(weather_data)
            if extreme_warning:
                response += f"{extreme_warning}\n\n"
            response += weather_service.format_weather_message(weather_data)

        if forecast_data:
            response += "\n\n📅 PRAKIRAAN CUACA 5 HARI:\n"
            for i, forecast in enumerate(forecast_data.get("forecasts", [])[:8:2]):
                response += f"   • {forecast['description'].capitalize()}\n"

        return response

    except Exception as e:
        logger.error(f"Error handling location message: {str(e)}")
        return "❌ Error: Tidak bisa memproses lokasi Anda."


def parse_telegram_update(update: dict):
    message = update.get("message") or update.get("edited_message")
    if not isinstance(message, dict) or "chat" not in message:
        return None, None, None, None

    chat_id = message["chat"].get("id")
    if chat_id is None:
        return None, None, None, None

    chat_id = str(chat_id)

    if message.get("photo"):
        photos = message.get("photo", [])
        if photos:
            largest_photo = max(photos, key=lambda item: item.get("file_size", 0))
            file_id = largest_photo.get("file_id")
            if file_id:
                file_path = telegram_client.get_file_path(file_id)
                if file_path:
                    media_url = telegram_client.get_file_url(file_path)
                    return chat_id, "image", None, media_url
        return chat_id, "image", None, None

    if message.get("location"):
        location = message["location"]
        latitude = location.get("latitude")
        longitude = location.get("longitude")
        return chat_id, "location", {"latitude": latitude, "longitude": longitude}, None

    text = message.get("text") or message.get("caption")
    if text:
        return chat_id, "text", text, None

    return chat_id, "unknown", None, None


async def main_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    Main webhook handler for all Telegram updates.
    """
    try:
        req_json = req.get_json()
        logger.info(f"Received webhook: {json.dumps(req_json, default=str)}")

        if not telegram_client.validate_webhook_payload(req_json):
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "Invalid payload"}),
                status_code=400,
                mimetype="application/json"
            )

        chat_id, message_type, payload, media_url = parse_telegram_update(req_json)
        if not chat_id:
            return func.HttpResponse(
                json.dumps({"status": "error", "message": "Invalid Telegram update"}),
                status_code=400,
                mimetype="application/json"
            )

        logger.info(f"Processing Telegram {message_type} update for chat {chat_id}")

        if message_type == "text":
            response_text = await handle_text_message(chat_id, payload)
        elif message_type == "image":
            if not media_url:
                response_text = "❌ Gagal mengambil foto. Silakan kirim ulang gambar tanaman Anda."
            else:
                response_text = await handle_image_message(chat_id, media_url)
        elif message_type == "location":
            location = payload or {}
            response_text = await handle_location_message(
                chat_id,
                location.get("latitude"),
                location.get("longitude")
            )
        else:
            response_text = (
                "📌 Maaf, saya hanya dapat memproses pesan teks, foto tanaman, atau lokasi saat ini. "
                "Silakan kirim pertanyaan, foto tanaman, atau lokasi Anda."
            )

        if response_text:
            success = telegram_client.send_text_message(chat_id, response_text)
            if not success:
                logger.error(f"Failed to send response to Telegram chat {chat_id}")

        return func.HttpResponse(
            json.dumps({"status": "success", "message": "Webhook processed", "chat_id": chat_id}),
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


@app.route(route="telegram_webhook", methods=["POST"])
async def telegram_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger for Telegram webhook.

    Webhook URL format:
    https://<function-app-name>.azurewebsites.net/api/telegram_webhook
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
