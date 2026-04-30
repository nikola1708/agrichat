"""
Plant diagnosis using Azure Vision API + Ollama LLM for disease analysis
"""
import logging
import requests
from typing import Optional, Dict, Any
import os
from io import BytesIO
from PIL import Image
import base64
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class PlantDiagnosisEngine:
    """Diagnose plant diseases using Azure Vision API + Ollama"""

    def __init__(self):
        self.vision_key = os.getenv("AZURE_VISION_KEY")
        self.vision_endpoint = os.getenv("AZURE_VISION_ENDPOINT")
        
        if not self.vision_key or not self.vision_endpoint:
            raise ValueError("AZURE_VISION_KEY and AZURE_VISION_ENDPOINT environment variables must be set")
        
        # Import ai_engine locally to get Ollama config
        from shared.ai_engine import get_ai_engine
        self.ai_engine = get_ai_engine()
        self.quota_exceeded_until = None

    def download_image(self, image_url: str) -> Optional[bytes]:
        """Download image from URL"""
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            return None

    def validate_plant_image(self, image_data: bytes) -> bool:
        """Validate if image contains plant"""
        try:
            img = Image.open(BytesIO(image_data))
            # Basic validation - check if image can be opened
            img.verify()
            return True
        except Exception as e:
            logger.error(f"Invalid image format: {str(e)}")
            return False

    def _get_fallback_diagnosis(self) -> Dict[str, Any]:
        """Provide fallback diagnosis when API quota is exceeded"""
        return {
            "plant_name": "Tanaman (Tidak teridentifikasi)",
            "health_status": "tidak pasti",
            "disease_name": "Tidak dapat dianalisis saat ini",
            "confidence": "0%",
            "symptoms": "Foto tidak dapat dianalisis karena keterbatasan sistem. Silakan coba lagi nanti atau hubungi dinas pertanian lokal untuk konsultasi gratis.",
            "nutrient_deficiency": "Tidak terdeteksi tanpa analisis",
            "treatment_recommendation": "Sementara menunggu, tips umum:\n• Pastikan tanaman mendapat air yang cukup (sesuai jenis tanaman)\n• Jangan over-watering\n• Berikan cahaya matahari minimal 6 jam/hari\n• Gunakan pupuk organik untuk nutrisi optimal",
            "urgency_level": "medium",
            "is_fallback": True
        }

    def analyze_plant_image(self, image_url: str) -> Dict[str, Any]:
        """Analyze plant image for disease diagnosis using Azure Vision + Ollama"""
        try:
            # Check if quota was recently exceeded
            if self.quota_exceeded_until and datetime.now() < self.quota_exceeded_until:
                logger.warning(f"API quota still exceeded, using fallback until {self.quota_exceeded_until}")
                return {
                    **self._get_fallback_diagnosis(),
                    "status": "fallback",
                    "image_url": image_url
                }
            
            # Download and validate image
            image_data = self.download_image(image_url)
            if not image_data:
                return {
                    "status": "error",
                    "message": "Gagal mengunduh foto. Pastikan koneksi internet baik dan coba lagi."
                }

            if not self.validate_plant_image(image_data):
                return {
                    "status": "error",
                    "message": "Format foto tidak valid. Silakan kirim foto tanaman dalam format JPG atau PNG."
                }

            # Step 1: Use Azure Vision API to describe the plant image
            image_description = self._analyze_with_azure_vision(image_data)
            if not image_description:
                return {
                    "status": "error",
                    "message": "Gagal menganalisis foto dengan Azure Vision. Silakan coba lagi."
                }

            # Step 2: Use Ollama to generate diagnosis based on the image description
            diagnosis_prompt = f"""Anda adalah ahli agronomi Indonesia. Analisis deskripsi tanaman ini dan berikan diagnosis:

DESKRIPSI FOTO:
{image_description}

Analisis sebagai ahli agronomi:

1. IDENTIFIKASI KONDISI:
   - Nama tanaman (jika terlihat)
   - Kondisi kesehatan (sehat/sakit/stres)
   - Tingkat keparahan (ringan/sedang/berat)

2. DIAGNOSIS PENYAKIT (jika ada):
   - Nama penyakit/hama
   - Keyakinan diagnosis (%)
   - Gejala utama yang terlihat

3. ANALISIS NUTRISI:
   - Nutrisi yang mungkin defisit
   - Indikasi visual

4. REKOMENDASI TINDAKAN:
   - Solusi konkret (dalam Bahasa Indonesia)
   - Obat/pupuk yang direkomendasikan
   - Langkah penyelamatan jika kritis

Berikan respons JSON dengan keys: plant_name, health_status, disease_name, confidence, symptoms, nutrient_deficiency, treatment_recommendation, urgency_level
"""

            response_text = self.ai_engine.generate_response(
                user_id="plant_diagnosis",
                message=diagnosis_prompt
            )

            # Parse JSON from response
            diagnosis_data = {}
            try:
                # Extract JSON from response if wrapped in markdown
                if response_text and "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                elif response_text and "{" in response_text:
                    start = response_text.find("{")
                    end = response_text.rfind("}") + 1
                    json_str = response_text[start:end]
                else:
                    json_str = response_text or "{}"

                if json_str:
                    diagnosis_data = json.loads(json_str)
            except json.JSONDecodeError:
                logger.warning("Could not parse JSON from Ollama response, using raw text")
                diagnosis_data = {"raw_analysis": response_text or "No analysis available"}

            diagnosis_data["status"] = "success"
            diagnosis_data["image_url"] = image_url

            logger.info(f"Plant diagnosis completed successfully")
            # Clear quota exceeded flag on success
            self.quota_exceeded_until = None
            return diagnosis_data

        except Exception as e:
            error_str = str(e)
            logger.error(f"Error analyzing plant image: {error_str}")
            
            # Check if this is a quota/rate limit error (429)
            if "429" in error_str or "quota" in error_str.lower() or "exceeded" in error_str.lower():
                logger.warning("Vision API quota exceeded, switching to fallback mode")
                # Set quota exceeded for 1 minute to avoid hammering API
                self.quota_exceeded_until = datetime.now() + timedelta(minutes=1)
                return {
                    **self._get_fallback_diagnosis(),
                    "status": "fallback",
                    "message": "⚠️ Sistem analisis gambar sedang dalam maintenance. Gunakan tips di bawah ini sementara menunggu.",
                    "image_url": image_url
                }
            
            return {
                "status": "error",
                "message": f"Gagal menganalisis foto: {error_str[:100]}"
            }

    def _analyze_with_azure_vision(self, image_data: bytes) -> Optional[str]:
        """Use Azure Computer Vision API to describe the plant image"""
        try:
            url = f"{self.vision_endpoint}/vision/v3.2/describe"
            headers = {
                "Ocp-Apim-Subscription-Key": self.vision_key,
                "Content-Type": "application/octet-stream"
            }
            params = {"maxCandidates": "1"}
            
            response = requests.post(
                url,
                headers=headers,
                params=params,
                data=image_data,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract description from Azure Vision response
            if "description" in result and "captions" in result["description"]:
                captions = result["description"]["captions"]
                if captions:
                    return captions[0].get("text", "")
            
            if "description" in result:
                return result["description"].get("text", "")
                
            return None
            
        except Exception as e:
            logger.error(f"Azure Vision API error: {str(e)}")
            return None

    def format_diagnosis_response(self, diagnosis: Dict[str, Any]) -> str:
        """Format diagnosis for Telegram message - casual & conversational"""
        if diagnosis.get("status") == "error":
            error_msg = diagnosis.get('message', 'Gagal menganalisis foto')
            return f"Hmm, ada masalah: {error_msg}\n\nSilakan coba kirim foto lagi atau hubungi support jika masalah berlanjut."

        lines = []
        
        # Add fallback notice if applicable
        if diagnosis.get("is_fallback"):
            lines.append("⚠️ Analisis Terbatas (Mode Offline)\n")
        else:
            lines.append("🔍 Hasil Analisis Tanaman Anda\n")

        # Natural conversational opening
        plant_name = diagnosis.get('plant_name', 'tanaman Anda')
        lines.append(f"Baik, saya lihat {plant_name}.")

        # Health status with emoji
        status = diagnosis.get("health_status", "unknown")
        if status == "sehat":
            lines.append("✅ Bagus! Tanaman ini terlihat sehat dan segar.")
        elif status == "stres":
            lines.append("⚠️ Tanaman menunjukkan tanda-tanda stres.")
        elif status == "sakit":
            lines.append("🚨 Tanaman ini tampak mengalami gangguan kesehatan.")
        else:
            lines.append(f"Status kesehatan: {status}")

        # Disease info if present
        disease = diagnosis.get("disease_name", "")
        if disease and disease != "Tidak terdeteksi":
            confidence = diagnosis.get("confidence", "?")
            lines.append(f"\n🦠 Kemungkinan masalah: {disease}")
            lines.append(f"Keyakinan: {confidence}")
            
            symptoms = diagnosis.get("symptoms", "")
            if symptoms:
                lines.append(f"Gejala yang terlihat: {symptoms}")

        # Nutrient deficiency
        nutrient = diagnosis.get("nutrient_deficiency", "")
        if nutrient and nutrient != "Tidak terdeteksi":
            lines.append(f"\n🌱 Kekurangan nutrisi: {nutrient}")

        # Treatment with casual tone
        treatment = diagnosis.get("treatment_recommendation", "")
        if treatment:
            lines.append(f"\n💡 Yang bisa kamu lakukan:")
            lines.append(treatment)

        # Urgency warning
        urgency = diagnosis.get("urgency_level", "")
        if urgency == "critical":
            lines.append("\n🚨 Ini penting! Ambil tindakan dalam 24 jam ke depan ya!")
        elif urgency == "high":
            lines.append("\n⚡ Sebaiknya ditangani segera dalam beberapa hari.")

        return "\n".join(lines)
