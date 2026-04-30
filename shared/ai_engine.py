"""
AI engine adapter supporting Ollama and LocalAI (basic).

This module provides a simple `AIEngine` class with a `generate_response`
method. It prefers `AI_ENGINE` environment variable to choose between
implementations. Defaults to `ollama` and expects a local Ollama server
running (default URL: http://localhost:11434).

Note: Endpoints for self-hosted LLM servers vary by version. This adapter
uses a best-effort HTTP call to common Ollama/OpenAI-compatible endpoints
and falls back to returning a readable error message if the call fails.
"""
import os
import logging
from typing import Optional
import requests
import json

logger = logging.getLogger(__name__)


def detect_indonesian(text: str) -> bool:
    """
    Detect if text is in Indonesian language.
    Uses common Indonesian words and patterns.
    """
    # Common Indonesian words/particles
    indonesian_keywords = [
        "yang", "untuk", "dengan", "dari", "adalah", "saya", "anda", "dia",
        "mereka", "kami", "kalian", "ini", "itu", "di", "ke", "pada", "oleh",
        "dan", "atau", "tidak", "ya", "ya", "gimana", "bagaimana", "berapa",
        "apa", "siapa", "mana", "kapan", "kenapa", "bagus", "baik", "buruk",
        "besar", "kecil", "banyak", "sedikit", "sudah", "belum", "akan", "bisa",
        "buat", "buatan", "tanam", "tanaman", "cuaca", "harga", "pasar", "petani",
        "padi", "jagung", "cabai", "bawang", "sayuran", "buah", "hasil", "panen",
        "lahan", "sawah", "ladang", "kebun", "tani", "berkebun", "bertani",
        "asalah", "bantuan", "membantu", "tolong", "mohon", "dimohon",
        "halo", "hai", "pagi", "siang", "sore", "malam", "assalamualaikum",
        "walaikumassalam", "terima", "kasih", "sama", "makasih", "ok", "okeh",
        "terimakasih", "selamat", "sampai", "jumpa", "bye", "baiklah", "baik"
    ]
    
    # Convert to lowercase and split into words
    text_lower = text.lower()
    words = text_lower.split()
    
    # Count Indonesian keywords found
    indonesian_count = sum(1 for word in words if any(keyword in word for keyword in indonesian_keywords))
    
    # If at least 30% of meaningful words are Indonesian keywords, consider it Indonesian
    if len(words) > 0:
        ratio = indonesian_count / len(words)
        return ratio > 0.2 or indonesian_count >= 2
    
    # Also check for common Indonesian patterns or specific characters
    # If text contains Latin characters and some Indonesian patterns, likely Indonesian
    if indonesian_count >= 1:
        return True
    
    return False


class AIEngine:
    def __init__(self):
        self.engine = os.getenv("AI_ENGINE", "ollama").lower()
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "default")

    def generate_response(self, user_id: str, message: str, weather_data: Optional[dict] = None, price_data: Optional[dict] = None) -> str:
        """Generate a response from the selected local AI engine.

        Args:
            user_id: The Telegram chat id (used to keep per-user context hints).
            message: The user message to send to the model.
            weather_data: Optional weather context data.
            price_data: Optional price context data.

        Returns:
            The model's textual reply, or an error/fallback message.
        """
        if self.engine == "ollama":
            return self._call_ollama(user_id, message, weather_data, price_data)
        if self.engine == "localai":
            return self._call_localai(user_id, message, weather_data, price_data)
        return "❌ AI engine tidak didukung. Set AI_ENGINE ke 'ollama' atau 'localai'."

    def _call_ollama(self, user_id: str, message: str, weather_data: Optional[dict] = None, price_data: Optional[dict] = None) -> str:
        url = f"{self.ollama_url}/api/generate"
        
        # Build context for system prompt
        context_info = ""
        if weather_data:
            context_info += f"\nKondisi cuaca saat ini: Suhu {weather_data.get('temperature')}°C, {weather_data.get('description', 'tidak diketahui')}, Kelembaban {weather_data.get('humidity')}%, Angin {weather_data.get('wind_speed')} m/s"
        if price_data:
            trending_up = [k for k, v in price_data.items() if isinstance(v, dict) and v.get('trend') == 'up']
            trending_down = [k for k, v in price_data.items() if isinstance(v, dict) and v.get('trend') == 'down']
            if trending_up:
                context_info += f"\nHarga sedang naik: {', '.join(trending_up)}"
            if trending_down:
                context_info += f"\nHarga sedang turun: {', '.join(trending_down)}"
        
        system_prompt = f"""Anda adalah asisten pertanian Indonesia yang berpengalaman dan ramah.
Jawab pertanyaan user dengan NATURAL, DETAIL, dan NYAMBUNG sesuai apa yang ditanya.
Jangan terlalu singkat, berikan penjelasan yang masuk akal dengan contoh tanaman spesifik.
Gunakan data cuaca dan harga yang tersedia untuk memberikan rekomendasi konkret.
Jika user tanya soal cuaca dan tanam, jawab: apakah cocok/tidak, tanaman apa yang bagus, dan ALASAN SPESIFIK.
Berikan jawaban yang terasa like ngobrol dengan petani, tidak generic.{context_info}"""
        
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\nPetani: {message}",
            "max_tokens": 300,  # Naikkan untuk jawaban lebih lengkap
            "stream": True,
            "temperature": 0.6,  # Naikkan untuk jawaban lebih natural dan conversational
        }

        try:
            resp = requests.post(url, json=payload, timeout=60, stream=True)
            resp.raise_for_status()
            
            # Collect all streaming chunks
            full_response = ""
            
            # Read streaming response line by line (JSONL format)
            for line in resp.iter_lines():
                if not line:
                    continue
                
                try:
                    chunk = json.loads(line)
                    
                    # Extract the response text from this chunk
                    if "response" in chunk:
                        full_response += chunk["response"]
                    
                    # Check if streaming is done
                    if chunk.get("done", False):
                        logger.debug(f"Ollama streaming complete. Total response length: {len(full_response)}")
                        break
                        
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON chunk: {line}")
                    continue
            
            if full_response:
                return full_response.strip()
            else:
                return "Maaf, saya tidak bisa memberi jawaban. Silakan coba lagi."
                
        except requests.exceptions.ReadTimeout as e:
            logger.error(f"Ollama request timed out: {e}")
            return "Koneksi timeout. Coba lagi dalam beberapa saat."
        except requests.RequestException as e:
            logger.error(f"Ollama request failed: {e}")
            return f"Gagal terhubung ke Ollama: {e}"

    def _call_localai(self, user_id: str, message: str, weather_data: Optional[dict] = None, price_data: Optional[dict] = None) -> str:
        # LocalAI aims to be OpenAI-compatible on /v1 endpoints
        url = os.getenv("LOCALAI_URL", "http://localhost:8080/v1/chat/completions")
        
        # Build context for system prompt
        context_info = ""
        if weather_data:
            context_info += f"\nKondisi cuaca saat ini: Suhu {weather_data.get('temperature')}°C, {weather_data.get('description', 'tidak diketahui')}, Kelembaban {weather_data.get('humidity')}%, Angin {weather_data.get('wind_speed')} m/s"
        if price_data:
            trending_up = [k for k, v in price_data.items() if isinstance(v, dict) and v.get('trend') == 'up']
            trending_down = [k for k, v in price_data.items() if isinstance(v, dict) and v.get('trend') == 'down']
            if trending_up:
                context_info += f"\nHarga sedang naik: {', '.join(trending_up)}"
            if trending_down:
                context_info += f"\nHarga sedang turun: {', '.join(trending_down)}"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": f"Anda adalah asisten pertanian Indonesia yang berpengalaman dan ramah. Jawab pertanyaan user dengan NATURAL, DETAIL, dan NYAMBUNG sesuai apa yang ditanya. Berikan penjelasan yang masuk akal dengan contoh tanaman spesifik. Gunakan data cuaca dan harga untuk rekomendasi konkret.{context_info}"},
                {"role": "user", "content": message}
            ],
            "max_tokens": 300,
        }

        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            # OpenAI-style response
            choices = data.get("choices") or []
            if choices:
                first = choices[0]
                if isinstance(first.get("message"), dict):
                    return first["message"].get("content", str(data))
                return first.get("text", str(data))
            return str(data)
        except requests.RequestException as e:
            logger.error(f"LocalAI request failed: {e}")
            return f"Gagal terhubung ke LocalAI: {e}"


# Factory
def get_ai_engine() -> AIEngine:
    return AIEngine()
