"""
Weather data integration with OpenWeatherMap API
"""
import logging
import requests
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)


class WeatherService:
    """Fetch and process weather data from OpenWeatherMap"""

    def __init__(self):
        self.api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5"

    def get_current_weather(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """Get current weather for given coordinates"""
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured")
            return None

        try:
            url = f"{self.base_url}/weather"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "units": "metric",
                "lang": "id"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Weather data retrieved for ({latitude}, {longitude})")

            return {
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "weather": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "wind_speed": data["wind"]["speed"],
                "clouds": data["clouds"]["all"],
                "rain": data.get("rain", {}).get("1h", 0),
                "sunrise": data["sys"]["sunrise"],
                "sunset": data["sys"]["sunset"]
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather data: {str(e)}")
            return None

    def get_forecast(self, latitude: float, longitude: float, days: int = 5) -> Optional[Dict[str, Any]]:
        """Get weather forecast for next 5 days (3-hour intervals)"""
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured")
            return None

        try:
            url = f"{self.base_url}/forecast"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "units": "metric",
                "lang": "id"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Weather forecast retrieved for ({latitude}, {longitude})")

            # Process forecast data
            forecasts = []
            for item in data["list"][:40]:  # Limit to 5 days
                forecasts.append({
                    "dt": item["dt"],
                    "temperature": item["main"]["temp"],
                    "humidity": item["main"]["humidity"],
                    "weather": item["weather"][0]["main"],
                    "description": item["weather"][0]["description"],
                    "rain_probability": item.get("pop", 0),
                    "rain_amount": item.get("rain", {}).get("3h", 0),
                    "wind_speed": item["wind"]["speed"]
                })

            return {
                "city": data["city"]["name"],
                "country": data["city"]["country"],
                "timezone": data["city"]["timezone"],
                "forecasts": forecasts
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather forecast: {str(e)}")
            return None

    def detect_extreme_weather(self, weather: Dict[str, Any]) -> Optional[str]:
        """Detect if there's extreme weather warning"""
        try:
            # Check for extreme conditions
            if weather.get("weather") in ["Thunderstorm", "Tornado", "Hurricane"]:
                return f"⚠️ PERINGATAN CUACA: {weather['description'].upper()}"

            if weather.get("rain", 0) > 50:  # Heavy rain
                return f"⚠️ HUJAN LEBAT DIPREDIKSI: {weather['rain']}mm"

            if weather.get("temperature", 0) > 40:  # Very hot
                return f"⚠️ PANAS EKSTREM: {weather['temperature']}°C"

            if weather.get("wind_speed", 0) > 10:  # Strong wind
                return f"⚠️ ANGIN KUAT: {weather['wind_speed']} m/s"

            return None
        except Exception as e:
            logger.error(f"Error detecting extreme weather: {str(e)}")
            return None

    def format_weather_message(self, weather: Dict[str, Any]) -> str:
        """Format weather data for WhatsApp message"""
        try:
            lines = ["🌤️ CUACA SAAT INI\n"]
            lines.append(f"Suhu: {weather['temperature']}°C (terasa {weather['feels_like']}°C)")
            lines.append(f"Kondisi: {weather['description'].capitalize()}")
            lines.append(f"Kelembaban: {weather['humidity']}%")
            lines.append(f"Angin: {weather['wind_speed']} m/s")
            lines.append(f"Awan: {weather['clouds']}%")

            if weather["rain"] > 0:
                lines.append(f"Hujan: {weather['rain']}mm")

            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Error formatting weather message: {str(e)}")
            return "Unable to format weather data"
