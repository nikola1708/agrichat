"""
Farm recommendation engine using Ollama LLM with fallback support
"""
import logging
import json
from typing import Dict, Any, Optional
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generate farming recommendations using Ollama LLM"""

    def __init__(self):
        # Import ai_engine locally to get Ollama config
        from shared.ai_engine import get_ai_engine
        self.ai_engine = get_ai_engine()
        self.response_cache = {}
        self.quota_exceeded_until = None

    def _get_fallback_recommendation(self, query: str, price_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Provide fallback recommendation when API quota is exceeded"""
        # Simple rule-based recommendations for common crops
        query_lower = query.lower()
        
        fallback_recs = {
            "top_recommendation": {
                "crop": "PADI",
                "confidence": "sedang",
                "reason": "Komoditas stabil sepanjang tahun dengan permintaan konsisten",
                "timing": "Tanam dalam 2-3 minggu",
                "expected_return": "Rp 3000-4000/kg"
            },
            "alternatives": [
                {
                    "crop": "JAGUNG",
                    "reason": "Alternatif dengan ROI menarik jika harga stabil",
                    "timing": "Musim penghujan optimal"
                },
                {
                    "crop": "SAYURAN DAUN (Bayam, Kangkung)",
                    "reason": "Panen cepat (30 hari), cocok untuk tambahan pendapatan",
                    "timing": "Bisa tanam kapan saja"
                }
            ],
            "to_avoid": [
                {
                    "crop": "CABAI MERAH",
                    "reason": "Harga sedang turun, risiko tinggi"
                }
            ],
            "action_items": [
                "Siapkan lahan dan kompos minimal 1 minggu sebelum tanam",
                "Monitor cuaca lokal sebelum menentukan jadwal tanam",
                "Hubungi dinas pertanian untuk info subsidi/bantuan bibit"
            ],
            "is_fallback": True
        }
        
        return fallback_recs

    def get_recommendation(
        self,
        query: str,
        weather_data: Optional[Dict[str, Any]] = None,
        price_data: Optional[Dict[str, Any]] = None,
        farmer_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate farming recommendation based on query and context
        
        Args:
            query: Farmer's question
            weather_data: Current weather data
            price_data: Current market prices
            farmer_context: Farmer profile and history
        
        Returns:
            Recommendation with plants, timing, and rationale
        """
        try:
            # Check if quota was recently exceeded
            if self.quota_exceeded_until and datetime.now() < self.quota_exceeded_until:
                logger.warning(f"API quota still exceeded, using fallback until {self.quota_exceeded_until}")
                return self._get_fallback_recommendation(query, price_data)
            
            # Build context message
            context_parts = []

            if weather_data:
                context_parts.append(f"KONDISI CUACA:\n{json.dumps(weather_data, ensure_ascii=False)}")

            if price_data:
                context_parts.append(f"HARGA PASAR TERKINI:\n{json.dumps(price_data, ensure_ascii=False)}")

            if farmer_context:
                context_parts.append(f"PROFIL PETANI:\n{json.dumps(farmer_context, ensure_ascii=False)}")

            context_str = "\n\n".join(context_parts)

            # Create system + recommendation prompt for Ollama
            recommendation_prompt = f"""Anda adalah ahli agronomi dan ekonomi pertanian Indonesia dengan 20+ tahun pengalaman.
Tugas Anda memberikan rekomendasi SPESIFIK, PRAKTIS, dan BERBASIS DATA untuk petani kecil Indonesia.

PRINSIP:
- JANGAN generic: Selalu referensi cuaca, harga, lokasi spesifik
- HINDARI komoditas dengan harga sedang jatuh (oversupply)
- UTAMAKAN komoditas dengan trend harga NAIK
- Pertimbangkan musim/cuaca ekstrem (El Niño/La Niña)
- Berikan TIMELINE konkret (minggu, bulan)
- Format BAHASA INDONESIA sederhana untuk petani grassroot

{context_str}

Pertanyaan petani: {query}

Berikan respons dalam format JSON dengan structure:
{{
  "top_recommendation": {{
    "crop": "NAMA TANAMAN",
    "confidence": "tinggi/sedang/rendah",
    "reason": "Penjelasan singkat",
    "timing": "Kapan tanam",
    "expected_return": "Estimasi hasil"
  }},
  "alternatives": [
    {{"crop": "...", "reason": "...", "timing": "..."}}
  ],
  "to_avoid": [
    {{"crop": "...", "reason": "..."}}
  ],
  "action_items": ["Langkah 1", "Langkah 2"]
}}
"""

            # Call Ollama via ai_engine
            response_text = self.ai_engine.generate_response(
                user_id="recommendation",
                message=recommendation_prompt
            )

            # Parse JSON from response
            try:
                # Extract JSON if wrapped in markdown
                if response_text and "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                elif response_text and "{" in response_text:
                    start = response_text.find("{")
                    end = response_text.rfind("}") + 1
                    json_str = response_text[start:end]
                else:
                    json_str = response_text or "{}"

                recommendation = json.loads(json_str) if json_str else {}
                recommendation["status"] = "success"
            except json.JSONDecodeError:
                recommendation = {
                    "status": "success",
                    "raw_recommendation": response_text or "No recommendation available"
                }

            logger.info(f"Recommendation generated successfully")
            # Clear quota exceeded flag on success
            self.quota_exceeded_until = None
            return recommendation

        except Exception as e:
            error_str = str(e)
            logger.error(f"Error generating recommendation: {error_str}")
            
            # Check if this is a quota/rate limit error (429)
            if "429" in error_str or "quota" in error_str.lower() or "exceeded" in error_str.lower():
                logger.warning("API quota exceeded, switching to fallback mode")
                # Set quota exceeded for 1 minute to avoid hammering API
                self.quota_exceeded_until = datetime.now() + timedelta(minutes=1)
                return {
                    **self._get_fallback_recommendation(query, price_data),
                    "status": "fallback",
                    "message": "⚠️ Sedang menggunakan rekomendasi offline. Respons terbatas namun tetap berguna untuk Anda."
                }
            
            return {
                "status": "error",
                "message": f"Failed to generate recommendation: {error_str}"
            }

    def format_recommendation_response(self, recommendation: Dict[str, Any]) -> str:
        """Format recommendation for Telegram message"""
        if recommendation.get("status") == "error":
            return f"❌ Error: {recommendation.get('message', 'Unknown error')}"

        # Add fallback notice if applicable
        lines = []
        if recommendation.get("status") == "fallback":
            lines.append("⚠️ REKOMENDASI OFFLINE (API sedang maintenance)\n")
            lines.append(recommendation.get("message", ""))
            lines.append("")

        if "raw_recommendation" in recommendation:
            return "\n".join(lines) + recommendation["raw_recommendation"] if lines else recommendation["raw_recommendation"]

        lines.append("🌾 REKOMENDASI TANAM\n")

        # Top recommendation
        if "top_recommendation" in recommendation:
            top = recommendation["top_recommendation"]
            lines.append(f"✅ PILIHAN TERBAIK: {top.get('crop', 'Unknown').upper()}")
            lines.append(f"   Keyakinan: {top.get('confidence', 'Unknown')}")
            lines.append(f"   Alasan: {top.get('reason', 'Unknown')}")
            lines.append(f"   Waktu tanam: {top.get('timing', 'Unknown')}")
            lines.append(f"   Estimasi hasil: {top.get('expected_return', 'Unknown')}\n")

        # Alternatives
        if "alternatives" in recommendation and recommendation["alternatives"]:
            lines.append("⚡ ALTERNATIF LAIN:")
            for alt in recommendation["alternatives"]:
                lines.append(f"   • {alt.get('crop', 'Unknown')}")
                lines.append(f"     Waktu: {alt.get('timing', 'Unknown')}\n")

        # To avoid
        if "to_avoid" in recommendation and recommendation["to_avoid"]:
            lines.append("⛔ HINDARI SEKARANG:")
            for avoid in recommendation["to_avoid"]:
                lines.append(f"   • {avoid.get('crop', 'Unknown')}: {avoid.get('reason', 'Unknown')}\n")

        # Action items
        if "action_items" in recommendation and recommendation["action_items"]:
            lines.append("📋 LANGKAH SELANJUTNYA:")
            for i, action in enumerate(recommendation["action_items"], 1):
                lines.append(f"   {i}. {action}")

        return "\n".join(lines)
