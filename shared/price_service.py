"""
Market price data integration
"""
import logging
import requests
from typing import Optional, Dict, Any, List
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class PriceService:
    """Fetch market price data from various sources"""

    def __init__(self):
        self.pihps_api_key = os.getenv("PIHPS_API_KEY")
        # PIHPS = Platform Informasi Harga Pangan Strategis (Indonesia)
        self.pihps_base_url = "https://hargapangan.id/api"

    def get_commodity_prices(self, commodity: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get current commodity prices
        
        Args:
            commodity: Specific commodity to fetch (e.g., 'padi', 'jagung')
        
        Returns:
            Price data with trends
        """
        try:
            # Mock data - replace with actual API calls when credentials available
            prices = {
                "padi": {
                    "name": "Padi",
                    "current_price": 3500,
                    "currency": "Rp/kg",
                    "trend": "up",
                    "change_percent": 5,
                    "highest_7days": 3600,
                    "lowest_7days": 3300
                },
                "jagung": {
                    "name": "Jagung",
                    "current_price": 2800,
                    "currency": "Rp/kg",
                    "trend": "down",
                    "change_percent": -3,
                    "highest_7days": 2900,
                    "lowest_7days": 2700
                },
                "cabai_merah": {
                    "name": "Cabai Merah",
                    "current_price": 8500,
                    "currency": "Rp/kg",
                    "trend": "down",
                    "change_percent": -10,
                    "highest_7days": 9500,
                    "lowest_7days": 8000
                },
                "bawang_merah": {
                    "name": "Bawang Merah",
                    "current_price": 15000,
                    "currency": "Rp/kg",
                    "trend": "up",
                    "change_percent": 8,
                    "highest_7days": 15500,
                    "lowest_7days": 14000
                },
                "kentang": {
                    "name": "Kentang",
                    "current_price": 4200,
                    "currency": "Rp/kg",
                    "trend": "stable",
                    "change_percent": 1,
                    "highest_7days": 4300,
                    "lowest_7days": 4100
                }
            }

            if commodity:
                return prices.get(commodity.lower())
            
            return prices

        except Exception as e:
            logger.error(f"Error fetching commodity prices: {str(e)}")
            return None

    def analyze_price_trend(self, commodity: str) -> Optional[str]:
        """Analyze price trend for a commodity"""
        try:
            prices = self.get_commodity_prices(commodity)
            
            if not prices:
                return None

            trend = prices.get("trend", "unknown")
            change = prices.get("change_percent", 0)
            price = prices.get("current_price", 0)

            if trend == "up":
                return f"📈 {prices['name']}: Naik {change}% - Harga bagus untuk dijual"
            elif trend == "down":
                return f"📉 {prices['name']}: Turun {change}% - Hindari tanam sekarang"
            else:
                return f"➡️ {prices['name']}: Stabil - Aman untuk ditanam"

        except Exception as e:
            logger.error(f"Error analyzing price trend: {str(e)}")
            return None

    def get_price_recommendation(self, commodities: List[str]) -> str:
        """Get price-based recommendation for multiple commodities"""
        try:
            lines = ["💰 ANALISIS HARGA PASAR\n"]
            
            recommend = []
            avoid = []

            for commodity in commodities:
                prices = self.get_commodity_prices(commodity)
                if prices:
                    if prices.get("trend") == "up":
                        recommend.append(f"{prices['name']}: Rp{prices['current_price']}/kg (↑ {prices['change_percent']}%)")
                    elif prices.get("trend") == "down":
                        avoid.append(f"{prices['name']}: Rp{prices['current_price']}/kg (↓ {prices['change_percent']}%)")

            if recommend:
                lines.append("✅ HARGA NAIK (Bagus dijual):")
                for item in recommend:
                    lines.append(f"   • {item}")

            if avoid:
                lines.append("\n❌ HARGA TURUN (Hindari sekarang):")
                for item in avoid:
                    lines.append(f"   • {item}")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error getting price recommendation: {str(e)}")
            return "Unable to fetch price data"
