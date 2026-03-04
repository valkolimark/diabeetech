"""
Insulin Command Parser for Voice Assistant
Handles comprehensive insulin logging voice commands

Migrated from itiflux voice_assistant/insulin_command_parser.py
- Removed PyQt5 dependencies
- All insulin types, number words, time references, body parts,
  regex patterns, and scoring preserved verbatim
"""

import re
from typing import Dict, Optional, Tuple, List
from datetime import datetime


class InsulinCommandParser:
    """Parser for insulin-related voice commands"""

    def __init__(self):
        # Define insulin types
        self.insulin_types = {
            # Categories
            'rapid': ['humalog', 'novolog', 'apidra', 'fiasp', 'admelog'],
            'fast': ['humalog', 'novolog', 'apidra', 'fiasp', 'admelog'],
            'short': ['regular', 'humulin r', 'novolin r'],
            'long': ['lantus', 'levemir', 'tresiba', 'basaglar', 'toujeo'],
            'basal': ['lantus', 'levemir', 'tresiba', 'basaglar', 'toujeo'],
            'bolus': ['humalog', 'novolog', 'apidra', 'fiasp', 'admelog'],

            # Specific brands
            'humalog': 'humalog',
            'novolog': 'novolog',
            'lantus': 'lantus',
            'levemir': 'levemir',
            'tresiba': 'tresiba',
            'apidra': 'apidra',
            'fiasp': 'fiasp',
            'admelog': 'admelog'
        }

        # Number words to values
        self.number_words = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
            'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
            'twenty-five': 25, 'twenty five': 25, 'twentyfive': 25,
            'thirty': 30, 'thirty-five': 35, 'thirty five': 35, 'thirtyfive': 35,
            'forty': 40, 'forty-five': 45, 'forty five': 45, 'fortyfive': 45,
            'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90,
            'hundred': 100, 'one hundred': 100
        }

        # Time references
        self.time_references = {
            'now': 'now',
            'morning': 'morning',
            'afternoon': 'afternoon',
            'evening': 'evening',
            'night': 'night',
            'breakfast': 'breakfast',
            'lunch': 'lunch',
            'dinner': 'dinner',
            'bedtime': 'bedtime',
            'before meal': 'before_meal',
            'after meal': 'after_meal',
            'with meal': 'with_meal'
        }

        # Body parts for injection sites
        self.body_parts = {
            'arm': 'arm',
            'leg': 'leg',
            'stomach': 'stomach',
            'abdomen': 'abdomen',
            'thigh': 'thigh',
            'upper arm': 'upper_arm',
            'belly': 'abdomen'
        }

        # Compile regex patterns for insulin commands
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for insulin detection"""
        # Main insulin action words
        insulin_actions = r'(?:log|record|add|took|take|inject(?:ed)?|gave|give|administer(?:ed)?|bolus(?:ed)?|shot)'

        # Insulin keywords
        insulin_keywords = r'(?:insulin|units?|shot|injection|dose|bolus|basal)'

        # Create main pattern for insulin detection
        self.insulin_pattern = re.compile(
            rf'(?:{insulin_actions}.*{insulin_keywords}|{insulin_keywords}.*{insulin_actions}|'
            rf'{insulin_actions}.*(?:{"|".join(self.insulin_types.keys())})|'
            rf'(?:{"|".join(self.insulin_types.keys())}).*{insulin_actions})',
            re.IGNORECASE
        )

        # Pattern for extracting amounts
        number_pattern = '|'.join(self.number_words.keys())
        self.amount_pattern = re.compile(
            rf'(?:(\d+(?:\.\d+)?)|({number_pattern}))\s*(?:units?)?',
            re.IGNORECASE
        )

        # Pattern for extracting insulin type
        type_pattern = '|'.join(self.insulin_types.keys())
        self.type_pattern = re.compile(
            rf'\b({type_pattern})\b(?:\s+insulin)?',
            re.IGNORECASE
        )

        # Pattern for time references
        time_pattern = '|'.join(self.time_references.keys())
        self.time_pattern = re.compile(
            rf'(?:at|for|during)?\s*\b({time_pattern})\b',
            re.IGNORECASE
        )

        # Pattern for body parts
        body_pattern = '|'.join(self.body_parts.keys())
        self.body_pattern = re.compile(
            rf'(?:in(?:\s+my)?|on(?:\s+my)?|at(?:\s+my)?)\s*\b({body_pattern})\b',
            re.IGNORECASE
        )

    def is_insulin_command(self, text: str) -> bool:
        """Check if the text is an insulin-related command"""
        return bool(self.insulin_pattern.search(text))

    def parse_insulin_command(self, text: str) -> Optional[Dict]:
        """Parse insulin command and extract components"""
        if not self.is_insulin_command(text):
            return None

        result = {
            'command_type': 'insulin',
            'units': None,
            'insulin_type': None,
            'time_reference': None,
            'injection_site': None,
            'original_text': text,
            'timestamp': datetime.now()
        }

        # Extract amount
        amount_match = self.amount_pattern.search(text)
        if amount_match:
            if amount_match.group(1):  # Numeric amount
                result['units'] = float(amount_match.group(1))
            elif amount_match.group(2):  # Word amount
                word = amount_match.group(2).lower()
                result['units'] = self.number_words.get(word, 0)

        # Extract insulin type
        type_match = self.type_pattern.search(text)
        if type_match:
            insulin_key = type_match.group(1).lower()
            if insulin_key in self.insulin_types:
                if isinstance(self.insulin_types[insulin_key], list):
                    # For categories, use the category name
                    result['insulin_type'] = insulin_key
                else:
                    # For specific brands
                    result['insulin_type'] = self.insulin_types[insulin_key]

        # Extract time reference
        time_match = self.time_pattern.search(text)
        if time_match:
            time_key = time_match.group(1).lower()
            result['time_reference'] = self.time_references.get(time_key, time_key)

        # Extract injection site
        body_match = self.body_pattern.search(text)
        if body_match:
            body_key = body_match.group(1).lower()
            result['injection_site'] = self.body_parts.get(body_key, body_key)

        # If no amount specified, check for common defaults
        if result['units'] is None:
            # Look for patterns like "my usual dose" or "normal dose"
            if re.search(r'\b(?:usual|normal|regular)\s+(?:dose|amount)\b', text, re.IGNORECASE):
                result['notes'] = 'usual dose'

        return result

    def differentiate_from_meal(self, text: str) -> str:
        """Determine if command is insulin or meal related"""
        # Check for clear insulin indicators
        if self.is_insulin_command(text):
            return 'insulin'

        # Check for meal indicators
        meal_keywords = r'\b(?:ate|eat|eating|had|having|breakfast|lunch|dinner|snack|meal|food|carbs?|grams?)\b'
        if re.search(meal_keywords, text, re.IGNORECASE):
            # Double-check it's not insulin with meal timing
            if not re.search(r'\b(?:insulin|units?|inject|shot)\b', text, re.IGNORECASE):
                return 'meal'

        return 'unknown'

    def generate_confirmation(self, parsed_data: Dict) -> str:
        """Generate a confirmation message for the parsed insulin command"""
        if not parsed_data:
            return "I couldn't understand the insulin command."

        parts = []

        # Amount
        if parsed_data['units']:
            parts.append(f"{parsed_data['units']} units")
        else:
            parts.append("insulin dose")

        # Type
        if parsed_data['insulin_type']:
            parts.append(f"of {parsed_data['insulin_type']}")

        # Time
        if parsed_data['time_reference']:
            if parsed_data['time_reference'] == 'now':
                parts.append("now")
            else:
                parts.append(f"at {parsed_data['time_reference']}")

        # Site
        if parsed_data['injection_site']:
            parts.append(f"in {parsed_data['injection_site']}")

        return f"Logging {' '.join(parts)}"

    def get_examples(self) -> List[str]:
        """Get example insulin commands"""
        return [
            "I took 6 units of humalog",
            "log 10 units of lantus",
            "record insulin shot 5 units",
            "took my insulin 8 units",
            "I injected 4 units in my stomach",
            "gave myself 12 units for breakfast",
            "insulin injection 15 units",
            "log rapid insulin 6 units",
            "took my basal insulin 20 units",
            "record 7 units now",
            "I took insulin at bedtime",
            "log insulin shot in arm",
            "bolused 5 units with meal",
            "my insulin dose was 9 units",
            "injected long acting insulin"
        ]
