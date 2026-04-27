"""
Plant diagnosis using OpenAI GPT-4 Vision
"""
import logging
import requests
from typing import Optional, Dict, Any
import os
from openai import OpenAI
from io import BytesIO
from PIL import Image
import base64

logger = logging.getLogger(__name__)


class PlantDiagnosisEngine:
    """Diagnose plant diseases using OpenAI GPT-4 Vision"""

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.vision_key = os.getenv("AZURE_VISION_KEY")
        self.vision_endpoint = os.getenv("AZURE_VISION_ENDPOINT")
        self.openai_client = OpenAI(api_key=api_key)
        self.model = "gpt-4-vision-preview"

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

    def analyze_plant_image(self, image_url: str) -> Dict[str, Any]:
        """Analyze plant image for disease diagnosis"""
        try:
            # Download and validate image
            image_data = self.download_image(image_url)
            if not image_data:
                return {
                    "status": "error",
                    "message": "Failed to download image"
                }

            if not self.validate_plant_image(image_data):
                return {
                    "status": "error",
                    "message": "Invalid image format"
                }

            # Convert to base64 for GPT-4o Vision
            image_base64 = base64.b64encode(image_data).decode("utf-8")

            # Call GPT-4o Vision for diagnosis
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": """Analisis foto tanaman ini sebagai ahli agronomi Indonesia:

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

Format respons sebagai JSON dengan keys: 
plant_name, health_status, disease_name, confidence, symptoms, 
nutrient_deficiency, treatment_recommendation, urgency_level
"""
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.7
            )

            # Parse response
            diagnosis_text = response.choices[0].message.content
            
            # Try to extract JSON if model returns it
            import json
            try:
                # Extract JSON from response if wrapped in markdown
                if diagnosis_text and "```json" in diagnosis_text:
                    json_str = diagnosis_text.split("```json")[1].split("```")[0].strip()
                elif diagnosis_text and "{" in diagnosis_text:
                    start = diagnosis_text.find("{")
                    end = diagnosis_text.rfind("}") + 1
                    json_str = diagnosis_text[start:end]
                else:
                    json_str = diagnosis_text or "{}"

                diagnosis_data = json.loads(json_str) if json_str else {}
            except:
                # If JSON parsing fails, return raw text
                diagnosis_data = {"raw_analysis": diagnosis_text or "No analysis available"}

            diagnosis_data["status"] = "success"
            diagnosis_data["image_url"] = image_url

            logger.info(f"Plant diagnosis completed successfully")
            return diagnosis_data

        except Exception as e:
            logger.error(f"Error analyzing plant image: {str(e)}")
            return {
                "status": "error",
                "message": f"Diagnosis failed: {str(e)}"
            }

    def format_diagnosis_response(self, diagnosis: Dict[str, Any]) -> str:
        """Format diagnosis for WhatsApp message"""
        if diagnosis.get("status") == "error":
            return f"❌ Error: {diagnosis.get('message', 'Unknown error')}"

        lines = ["🔍 ANALISIS FOTO TANAMAN\n"]

        if "plant_name" in diagnosis:
            lines.append(f"🌿 Tanaman: {diagnosis.get('plant_name', 'Unknown')}")

        if "health_status" in diagnosis:
            status_emoji = "✅" if diagnosis["health_status"] == "sehat" else "⚠️"
            lines.append(f"{status_emoji} Status: {diagnosis.get('health_status', 'Unknown')}")

        if "disease_name" in diagnosis:
            lines.append(f"🦠 Penyakit: {diagnosis.get('disease_name', 'Tidak terdeteksi')}")
            if "confidence" in diagnosis:
                lines.append(f"   Keyakinan: {diagnosis.get('confidence')}%")

        if "symptoms" in diagnosis:
            lines.append(f"📋 Gejala: {diagnosis.get('symptoms')}")

        if "nutrient_deficiency" in diagnosis:
            lines.append(f"🥗 Nutrisi: {diagnosis.get('nutrient_deficiency')}")

        if "treatment_recommendation" in diagnosis:
            lines.append(f"\n💡 Rekomendasi:")
            treatment = diagnosis.get('treatment_recommendation') or "Not available"
            lines.append(treatment)

        if "urgency_level" in diagnosis:
            urgency = diagnosis.get('urgency_level')
            if urgency == "critical":
                lines.append("\n🚨 URGENSI: TINGGI - Ambil tindakan segera!")

        return "\n".join(lines)
