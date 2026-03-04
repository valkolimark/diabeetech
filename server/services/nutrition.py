"""
OpenAI + USDA nutrition query service.
Handles food/nutrition queries via ChatGPT and USDA FoodData Central.
"""
import json
import logging
import os
from typing import Optional

logger = logging.getLogger("diabeetech.nutrition")


class NutritionService:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.usda_key = os.getenv("USDA_API_KEY")

    async def query(self, text: str) -> str:
        """
        Process a nutrition query using OpenAI GPT.
        Returns a natural language response.
        """
        if not self.openai_key:
            return "OpenAI API key not configured."

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.openai_key)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a diabetes nutrition assistant. "
                            "Answer questions about carb counts, nutrition facts, and food choices "
                            "in a concise, helpful way. Focus on carbohydrate content since the user "
                            "is managing diabetes. Keep responses under 3 sentences."
                        )
                    },
                    {"role": "user", "content": text}
                ],
                max_tokens=200,
                temperature=0.7,
            )

            return response.choices[0].message.content or "I couldn't find nutrition info for that."
        except Exception as e:
            logger.error(f"Nutrition query error: {e}")
            return f"Sorry, I couldn't look that up right now."
