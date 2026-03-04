"""
Food command parser.
Handles voice commands for nutrition queries.
"""
import re
import logging

logger = logging.getLogger("diabeetech.voice.parsers.food")

# Patterns that indicate a nutrition/food query
FOOD_PATTERNS = [
    re.compile(r'how\s+many\s+(?:carbs|calories|carbohydrates)', re.IGNORECASE),
    re.compile(r'(?:what|how)\s+(?:is|are)\s+the\s+(?:carbs|nutrition|calories)', re.IGNORECASE),
    re.compile(r'(?:carbs|calories|nutrition)\s+(?:in|for|of)', re.IGNORECASE),
    re.compile(r'(?:look\s+up|find|search|what\'?s?\s+in)', re.IGNORECASE),
]


def parse_food_command(text: str) -> dict | None:
    """
    Parse a food/nutrition query from text.

    Returns:
        dict with keys:
            action: "nutrition_query"
            query: the food query text
        None if not a food command
    """
    for pattern in FOOD_PATTERNS:
        if pattern.search(text):
            return {
                "action": "nutrition_query",
                "query": text,
            }
    return None
