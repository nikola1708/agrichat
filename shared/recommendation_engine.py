"""
Farm recommendation engine using OpenAI GPT-4
"""
import logging
import json
from typing import Dict, Any, Optional
from openai import OpenAI
import os

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generate farming recommendations using OpenAI GPT-4"""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.openai_client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")

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
            # Build context message
            context_parts = []

            if weather_data:
                context_parts.append(f"KONDISI CUACA:\n{json.dumps(weather_data, ensure_ascii=False)}")

            if price_data:
                context_parts.append(f"HARGA PASAR TERKINI:\n{json.dumps(price_data, ensure_ascii=False)}")

            if farmer_context:
                context_parts.append(f"PROFIL PETANI:\n{json.dumps(farmer_context, ensure_ascii=False)}")

            context_str = "\n\n".join(context_parts)

            # Create system prompt
            system_prompt = """Anda adalah ahli agronomi dan ekonomi pertanian Indonesia dengan 20+ tahun pengalaman.
Tugas Anda memberikan rekomendasi SPESIFIK, PRAKTIS, dan BERBASIS DATA untuk petani kecil Indonesia.

PRINSIP:
- JANGAN generic: Selalu referensi cuaca, harga, lokasi spesifik
- HINDARI komoditas dengan harga sedang jatuh (oversupply)
- UTAMAKAN komoditas dengan trend harga NAIK
- Pertimbangkan musim/cuaca ekstrem (El Niño/La Niña)
- Berikan TIMELINE konkret (minggu, bulan)
- Format BAHASA INDONESIA sederhana untuk petani grassroot

FORMAT RESPONS:
```json
{
  "top_recommendation": {
    "crop": "NAMA TANAMAN",
    "confidence": "tinggi/sedang/rendah",
    "reason": "Penjelasan singkat mengapa (cuaca/harga/musim)",
    "timing": "Kapan tanam (hari/minggu ke depan)",
    "expected_return": "Estimasi hasil/harga"
  },
  "alternatives": [
    {
      "crop": "TANAMAN ALTERNATIF",
      "reason": "Mengapa dipertimbangkan",
      "timing": "Waktu tanam"
    }
  ],
  "to_avoid": [
    {
      "crop": "TANAMAN DIHINDARI",
      "reason": "Mengapa hindari (harga jatuh/cuaca jelek)"
    }
  ],
  "action_items": [
    "Langkah konkret 1",
    "Langkah konkret 2"
  ]
}
```
"""

            # Call GPT-4o
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{context_str}\n\nPertanyaan petani: {query}"}
                ],
                max_tokens=1500,
                temperature=0.7
            )

            response_text = response.choices[0].message.content

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
            return recommendation

        except Exception as e:
            logger.error(f"Error generating recommendation: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to generate recommendation: {str(e)}"
            }

    def format_recommendation_response(self, recommendation: Dict[str, Any]) -> str:
        """Format recommendation for WhatsApp message"""
        if recommendation.get("status") == "error":
            return f"❌ Error: {recommendation.get('message', 'Unknown error')}"

        if "raw_recommendation" in recommendation:
            return recommendation["raw_recommendation"]

        lines = ["🌾 REKOMENDASI TANAM\n"]

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
