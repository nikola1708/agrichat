"""AI engine adapter supporting llama.cpp (fast local) and Ollama.

This module provides a simple `AIEngine` class with a `generate_response`
method. The primary recommended engine is 'llamacpp' for fast local inference.

Configuration via environment variables:
- AI_ENGINE: 'llamacpp' (default, recommended) or 'ollama'
- For llamacpp:
  - LLAMACPP_MODEL_PATH: path to .gguf model file
  - LLAMACPP_N_CTX: context size (default: 512)
  - LLAMACPP_N_THREADS: CPU threads (default: auto-detect)
  
- For Ollama:
  - OLLAMA_URL: default http://localhost:11434
  - OLLAMA_MODEL: model name (e.g., 'mistral')
"""
import os
import logging
from typing import Optional
import requests
import json

logger = logging.getLogger(__name__)

# Global llama.cpp instance (lazy loaded)
_llama_instance = None


def detect_indonesian(text: str) -> bool:
    """Detect if text is in Indonesian language."""
    indonesian_keywords = [
        "yang", "untuk", "dengan", "dari", "adalah", "saya", "anda", "dia",
        "mereka", "kami", "kalian", "ini", "itu", "di", "ke", "pada", "oleh",
        "dan", "atau", "tidak", "ya", "gimana", "bagaimana", "berapa",
        "apa", "siapa", "mana", "kapan", "kenapa", "bagus", "baik", "buruk",
        "besar", "kecil", "banyak", "sedikit", "sudah", "belum", "akan", "bisa",
        "buat", "tanam", "tanaman", "cuaca", "harga", "pasar", "petani",
        "padi", "jagung", "cabai", "bawang", "sayuran", "buah", "hasil", "panen",
        "lahan", "sawah", "ladang", "kebun", "tani", "berkebun", "bertani",
        "bantuan", "membantu", "tolong", "mohon",
        "halo", "hai", "pagi", "siang", "sore", "malam", "assalamualaikum",
        "terima", "kasih", "sama", "makasih", "ok", "okeh", "selamat", "sampai"
    ]
    
    text_lower = text.lower()
    words = text_lower.split()
    indonesian_count = sum(1 for word in words if any(kw in word for kw in indonesian_keywords))
    
    if len(words) > 0:
        return (indonesian_count / len(words)) > 0.2 or indonesian_count >= 2
    return indonesian_count >= 1


def _get_rag_context(message: str) -> str:
    """Retrieve RAG context from FAISS index if available."""
    try:
        from shared import retriever
        top_k = int(os.getenv('RAG_TOP_K', '3'))
        retrieved = retriever.retrieve(message, top_k=top_k)
        if retrieved:
            snippets = '\n\n'.join([f"[{i+1}] {r[1][:200]}" for i, r in enumerate(retrieved)])
            return f"\n\n📚 Referensi:\n{snippets}"
    except Exception as e:
        logger.debug(f"RAG retrieval skipped: {e}")
    return ""


def _get_context_info(weather_data: Optional[dict] = None, price_data: Optional[dict] = None) -> str:
    """Build context string from weather and price data."""
    context = ""
    if weather_data:
        context += f"\n🌤️ Cuaca: {weather_data.get('temperature')}°C, {weather_data.get('description', '?')}, Kelembaban {weather_data.get('humidity')}%, Angin {weather_data.get('wind_speed')} m/s"
    if price_data:
        trending_up = [k for k, v in price_data.items() if isinstance(v, dict) and v.get('trend') == 'up']
        trending_down = [k for k, v in price_data.items() if isinstance(v, dict) and v.get('trend') == 'down']
        if trending_up or trending_down:
            context += f"\n💰 Harga: "
            if trending_up:
                context += f"↗️ {', '.join(trending_up)} "
            if trending_down:
                context += f"↘️ {', '.join(trending_down)}"
    return context


class AIEngine:
    def __init__(self):
        self.engine = os.getenv("AI_ENGINE", "llamacpp").lower()
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "mistral:latest")
        self.llamacpp_model_path = os.getenv("LLAMACPP_MODEL_PATH")

    def generate_response(self, user_id: str, message: str, weather_data: Optional[dict] = None, price_data: Optional[dict] = None) -> str:
        """Generate response from selected AI engine."""
        if self.engine == "llamacpp":
            return self._call_llamacpp(message, weather_data, price_data)
        elif self.engine == "ollama":
            return self._call_ollama(message, weather_data, price_data)
        return f"❌ Engine '{self.engine}' tidak didukung. Pilih: llamacpp atau ollama."

    def _call_llamacpp(self, message: str, weather_data: Optional[dict] = None, price_data: Optional[dict] = None) -> str:
        """Call local llama.cpp model for fast inference."""
        global _llama_instance
        
        try:
            from llama_cpp import Llama
        except ImportError:
            return "❌ llama-cpp-python belum terinstall. Jalankan: pip install llama-cpp-python"

        # Initialize llama.cpp instance once
        if _llama_instance is None:
            if not self.llamacpp_model_path or not os.path.exists(self.llamacpp_model_path):
                return (
                    "❌ Model tidak ditemukan di LLAMACPP_MODEL_PATH. "
                    "Silakan download model .gguf terlebih dahulu (lihat LLAMA_CPP_SETUP.md)"
                )
            
            try:
                n_ctx = int(os.getenv("LLAMACPP_N_CTX", "512"))
                n_threads = int(os.getenv("LLAMACPP_N_THREADS", "0"))  # 0 = auto
                n_gpu_layers = int(os.getenv("LLAMACPP_N_GPU_LAYERS", "0"))  # GPU support (optional)
                
                logger.info(f"Loading llama.cpp model: {self.llamacpp_model_path}")
                _llama_instance = Llama(
                    model_path=self.llamacpp_model_path,
                    n_ctx=n_ctx,
                    n_threads=n_threads if n_threads > 0 else None,
                    n_gpu_layers=n_gpu_layers,
                    verbose=False
                )
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load llama.cpp model: {e}")
                return f"❌ Gagal memuat model: {e}"

        # Build system prompt with RAG + context
        context_info = _get_context_info(weather_data, price_data)
        rag_context = _get_rag_context(message)
        
        system_prompt = f"""Anda adalah asisten pertanian Indonesia yang berpengalaman, ramah, dan praktis.

PRINSIP JAWABAN:
• Jawab LANGSUNG & SINGKAT (2-3 kalimat pembukaan, detail di paragraph berikutnya)
• NATURAL: seperti ngobrol dengan petani, gunakan bahasa sederhana
• SPESIFIK: beri contoh tanaman konkret, bukan general
• KONTEKSTUAL: gunakan data cuaca/harga untuk rekomendasi akurat
• ACTIONABLE: berikan langkah praktis yang bisa dilakukan

Jika ditanya tentang tanam saat cuaca tertentu:
→ Jawab: cocok/tidak cocok + ALASAN SPESIFIK + tanaman rekomendasi

Jika ditanya tentang harga:
→ Jawab: analisis singkat dari tren harga + strategi jual/beli{context_info}{rag_context}"""

        try:
            # Use llama.cpp in-process for fast inference
            response = _llama_instance(
                prompt=f"{system_prompt}\n\nPetani: {message}\nAsisten:",
                max_tokens=250,
                temperature=0.5,  # More deterministic for agriculture advice
                top_p=0.85,
                top_k=40,
                stop=["Petani:", "\n\n"],
                echo=False
            )
            
            answer = response["choices"][0]["text"].strip()
            if answer:
                return answer
            return "Maaf, tidak ada jawaban. Coba pertanyaan lain."
            
        except Exception as e:
            logger.error(f"llama.cpp inference failed: {e}")
            return f"❌ Error inference: {e}"

    def _call_ollama(self, message: str, weather_data: Optional[dict] = None, price_data: Optional[dict] = None) -> str:
        """Call Ollama (alternative, requires ollama server running)."""
        url = f"{self.ollama_url}/api/generate"
        
        context_info = _get_context_info(weather_data, price_data)
        rag_context = _get_rag_context(message)
        
        system_prompt = f"""Anda adalah asisten pertanian Indonesia yang ramah dan praktis.
Jawab dengan DETAIL tapi SINGKAT, gunakan contoh tanaman spesifik.
Gunakan konteks cuaca dan harga untuk rekomendasi akurat.{context_info}{rag_context}"""

        payload = {
            "model": self.ollama_model,
            "prompt": f"{system_prompt}\n\nPertanyaan: {message}",
            "max_tokens": 250,
            "stream": False,
            "temperature": 0.6,
        }

        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            result = data.get("response", "").strip()
            return result if result else "Maaf, tidak ada jawaban."
        except requests.exceptions.Timeout:
            return "⏱️ Request timeout. Coba lagi."
        except requests.RequestException as e:
            logger.error(f"Ollama error: {e}")
            return f"❌ Koneksi Ollama gagal: {e}"




def get_ai_engine() -> AIEngine:
    """Factory function to get AI engine."""
    return AIEngine()
