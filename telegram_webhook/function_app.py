
import azure.functions as func
import json
import logging
import os
from datetime import datetime
import random

# Import shared modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.cosmos_db import CosmosDBManager
from shared.ai_vision import PlantDiagnosisEngine
from shared.recommendation_engine import RecommendationEngine
from shared.weather_service import WeatherService
from shared.price_service import PriceService
from shared.telegram_api import TelegramAPIClient
from shared.ai_engine import detect_indonesian

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


def _normalize_text(text: str) -> str:
    """Normalize text for semantic intent detection - lowercase & trim"""
    return text.lower().strip()


def _detect_greeting(message: str) -> bool:
    """Detect casual greetings - case insensitive"""
    greetings = ["halo", "hai", "hello", "pagi", "siang", "sore", "malam", "apa kabar", 
                 "gimana", "assalamualaikum", "assalamu'alaikum", "waalaikumassalam",
                 "selamat pagi", "selamat siang", "selamat sore", "selamat malam", 
                 "halo!", "hai!", "hello!", "pagi!", "siang!", "sore!"]
    text_normalized = _normalize_text(message)
    
    # Log for debug
    logger.debug(f"Checking greeting for normalized text: '{text_normalized}'")
    
    # Check exact match first
    if text_normalized in greetings:
        logger.debug(f"Exact greeting match found: {text_normalized}")
        return True
    
    # Check substring match
    for greeting in greetings:
        if greeting in text_normalized:
            logger.debug(f"Greeting '{greeting}' found in '{text_normalized}'")
            return True
    
    logger.debug(f"No greeting detected for: {text_normalized}")
    return False


def _detect_help_request(message: str) -> bool:
    """Detect if user asking for help/menu - case insensitive"""
    help_keywords = ["bantuan", "help", "menu", "apa yang bisa", "bisa apa", 
                     "fitur apa", "gimana cara", "bagaimana cara", "tutorial"]
    text_normalized = _normalize_text(message)
    
    for keyword in help_keywords:
        if keyword in text_normalized:
            logger.debug(f"Help keyword '{keyword}' found in '{text_normalized}'")
            return True
    return False


def _detect_thanks(message: str) -> bool:
    """Detect gratitude - case insensitive"""
    thanks = ["terima kasih", "terimakasih", "thanks", "makasih", "thx", "tq", "thank you"]
    text_normalized = _normalize_text(message)
    
    for word in thanks:
        if word in text_normalized:
            logger.debug(f"Thanks keyword '{word}' found in '{text_normalized}'")
            return True
    return False


def _get_greeting_response() -> str:
    """Get casual greeting response"""
    responses = [
        "Halo! 👋 Apa kabar? Ada yang bisa aku bantu tentang pertanian atau tanahmu?",
        "Hai! 😊 Apa kabar? Mau tanya tentang tanaman, cuaca, atau harga komoditas?",
        "Halo petani! 🌾 Apa yang bisa aku bantu hari ini?",
        "Pagi! ☀️ Siap membantu pertanyaan pertanian mu. Ada yang perlu?",
    ]
    return random.choice(responses)


def _get_help_response() -> str:
    """Get help menu response"""
    return """📖 Aku bisa membantu dengan:\n
1️⃣ **Rekomendasi tanam** - Tanya "apa yang bagus ditanam sekarang?"
2️⃣ **Analisis foto tanaman** - Kirim foto tanaman, aku bisa analisis penyakit & nutrisi
3️⃣ **Info cuaca** - Tanya "bagaimana cuaca hari ini?"
4️⃣ **Harga pasar** - Tanya "berapa harga padi/jagung?" 
5️⃣ **Tips bertani** - Tanya "tips bertani jagung" atau apapun

💡 Atau cukup kirim pesan natural, aku akan paham maksudmu!
📍 Kirim lokasi kamu agar rekomendasi lebih akurat."""


def _get_thanks_response() -> str:
    """Get gratitude response"""
    responses = [
        "Sama-sama! 😊 Semoga panenmu lancar ya!",
        "Senang bisa membantu! 🌾 Jangan ragu tanya lagi kalau ada yang perlu.",
        "Dengan senang hati! 🤝 Semoga tanamanmu berkembang baik!",
    ]
    import random
    return random.choice(responses)


def _should_include_weather(message: str) -> bool:
    """Check if user is asking about weather"""
    weather_keywords = [
        "cuaca", "suhu", "angin", "kelembaban", "hujan", "cerah", "awan",
        "prakiraan", "forecast", "mendung", "panas", "dingin", "kabut",
        "bagaimana cuaca", "apa cuaca", "cuaca hari ini", "kondisi cuaca",
        "temp", "temperature", "wind", "humidity"
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in weather_keywords)


def _should_include_prices(message: str) -> bool:
    """Check if user is asking about prices or market"""
    price_keywords = [
        "harga", "pasar", "mahal", "murah", "cerai", "harganya", "berapa harga",
        "berapa harganya", "harga sekarang", "harga hari ini", "analisis harga",
        "trend harga", "naik turun", "price", "market", "ekonomi", "menguntungkan"
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in price_keywords)


async def handle_text_message(chat_id: str, message: str) -> str:
    """
    Handle incoming text messages from Telegram - with casual conversation.
    Only processes Indonesian language messages.
    """
    try:
        logger.info(f"Processing text message from {chat_id}: {message[:50]}...")

        # Check if message is in Indonesian language
        if not detect_indonesian(message):
            logger.info(f"Non-Indonesian message detected from {chat_id}: {message[:30]}")
            return "Maaf, saya hanya bisa mengerti bahasa Indonesia. 🇮🇩\n\nSilakan tulis pesan dalam bahasa Indonesia ya!"

        # Handle casual interactions - with error handling
        try:
            is_greeting = _detect_greeting(message)
            logger.info(f"Greeting detection result: {is_greeting} for message: {message}")
            if is_greeting:
                response = _get_greeting_response()
                logger.info(f"Greeting detected, returning: {response[:50]}")
                return response
        except Exception as e:
            logger.warning(f"Error in greeting detection: {str(e)}")
        
        try:
            is_help = _detect_help_request(message)
            logger.info(f"Help detection result: {is_help} for message: {message}")
            if is_help:
                return _get_help_response()
        except Exception as e:
            logger.warning(f"Error in help detection: {str(e)}")
        
        try:
            is_thanks = _detect_thanks(message)
            logger.info(f"Thanks detection result: {is_thanks} for message: {message}")
            if is_thanks:
                return _get_thanks_response()
        except Exception as e:
            logger.warning(f"Error in thanks detection: {str(e)}")

        # Process farming-related questions
        logger.info(f"Processing as farming question for: {message}")
        farmer_profile = cosmos_db.get_farmer_profile(chat_id)
        latitude = farmer_profile.get("latitude", -6.2088) if farmer_profile else -6.2088
        longitude = farmer_profile.get("longitude", 106.8456) if farmer_profile else 106.8456

        weather_data = weather_service.get_current_weather(latitude, longitude)
        price_data = price_service.get_commodity_prices()

        # Use AI engine directly for quick, direct answers with context
        from shared.ai_engine import get_ai_engine
        ai_engine = get_ai_engine()
        response = ai_engine.generate_response(
            user_id=chat_id,
            message=message,
            weather_data=weather_data,
            price_data=price_data
        )

        history_entry = {
            "type": "text",
            "message": message,
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        }
        cosmos_db.save_diagnosis_history(chat_id, history_entry)

        return response

    except Exception as e:
        logger.error(f"Error handling text message: {str(e)}")
        return f"Maaf, ada kesalahan saat memproses pertanyaan: {str(e)[:100]}\n\nSilakan coba lagi atau hubungi support."


async def handle_image_message(chat_id: str, media_url: str) -> str:
    """
    Handle incoming image messages from Telegram - casual analysis response.
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
        return "Hmm, aku kesulitan menganalisis foto ini. Coba kirim foto yang lebih jelas ya, pastikan cahayanya cukup dan tanaman terlihat dengan baik. 📸"


async def handle_location_message(chat_id: str, latitude: float, longitude: float) -> str:
    """
    Handle location messages from Telegram - casual response.
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

        response = "✅ Lokasi disimpan! Sekarang rekomendasi saya jadi lebih akurat untuk wilayahmu.\n\n"

        if weather_data:
            extreme_warning = weather_service.detect_extreme_weather(weather_data)
            if extreme_warning:
                response += f"{extreme_warning}\n\n"
            response += weather_service.format_weather_message(weather_data)

        if forecast_data:
            response += "\n\n📅 Prakiraan 5 hari ke depan:\n"
            for i, forecast in enumerate(forecast_data.get("forecasts", [])[:8:2]):
                response += f"   • {forecast['description'].capitalize()}\n"

        return response

    except Exception as e:
        logger.error(f"Error handling location message: {str(e)}")
        return "Hmm, ada masalah saat memproses lokasi. Coba kirim ulang ya!"


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
                response_text = "Oops, aku gagal mengambil foto. Coba kirim ulang foto tanaman mu ya 📸"
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
                "Hmm, tipe pesan itu belum bisa aku proses. Aku bisa membantu dengan:\n"
                "📝 Pesan teks (pertanyaan pertanian)\n"
                "🖼️ Foto tanaman (untuk analisis penyakit)\n"
                "📍 Lokasi kamu (untuk cuaca & rekomendasi akurat)\n\n"
                "Coba kirim salah satu! 😊"
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
