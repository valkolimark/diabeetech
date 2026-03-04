"""
Intent classifier for better query vs command differentiation
Uses a scoring system to determine user intent

Migrated from itiflux voice_assistant/intent_classifier.py
- Removed PyQt5 dependencies
- ALL 4-category scoring weights and patterns preserved verbatim
- Uses local corrections import instead of voice_assistant.stt_post_processor
"""

import re
from typing import Dict, Tuple
from voice.corrections import STTPostProcessor


class IntentClassifier:
    """Classify voice commands as queries or logging commands"""

    def __init__(self):
        # Initialize STT post-processor
        self.stt_processor = STTPostProcessor()

        # Words that should NEVER be treated as food
        self.non_food_blacklist = {
            'timer', 'timers', 'countdown', 'countdowns',
            'alarm', 'alarms', 'reminder', 'reminders',
            'setting', 'settings', 'feature', 'features',
            'button', 'buttons', 'screen', 'display',
            'the', 'a', 'an', 'of', 'for', 'with',
            'delete', 'remove', 'clear', 'cancel', 'stop',
            'time', 'clock', 'duration', 'period'
        }

        # Insulin logging patterns - high priority
        self.insulin_patterns = [
            # X units of insulin patterns
            (r'\b\d+(\.\d+)?\s*units?\s+of\s+insulin\b', 10),
            (r'\b(two|three|four|five|six|seven|eight|nine|ten)\s+units?\s+of\s+insulin\b', 10),

            # "X more units" patterns
            (r'\b\d+(\.\d+)?\s*more\s+units?\s+of\s+insulin\b', 10),
            (r'\b(two|three|four|five|six|seven|eight|nine|ten)\s+more\s+units?\s+of\s+insulin\b', 10),
            (r'\bmore\s+units?\s+of\s+insulin\b', 8),
            # Simple "X more units" without "of insulin"
            (r'\b\d+(\.\d+)?\s*more\s+units?\b', 8),
            (r'\b(two|three|four|five|six|seven|eight|nine|ten)\s+more\s+units?\b', 8),

            # Common insulin logging phrases
            (r'\b(took|had|just\s+took|just\s+had|logged|log|given)\s+.*units?\s+of\s+insulin\b', 10),
            (r'\bi\s+(took|had|just\s+took|just\s+had)\s+.*units?\s+of\s+insulin\b', 10),

            # Simple patterns
            (r'\btook\s+insulin\b', 8),
            (r'\bhad\s+insulin\b', 8),
            (r'\blogged?\s+.*insulin\b', 8),

            # Insulin with numbers
            (r'\binsulin.*\d+(\.\d+)?\s*units?\b', 8),
            (r'\b\d+(\.\d+)?\s*units?\s+.*insulin\b', 8),

            # With insulin types
            (r'\b(humalog|novolog|lantus|tresiba|apidra|fiasp|levemir|basaglar)\b', 8),
            (r'\b\d+(\.\d+)?\s*units?\s+of\s+(humalog|novolog|lantus|tresiba|apidra|fiasp|levemir|basaglar)\b', 10),
        ]

        # Timer control patterns - highest priority
        self.timer_patterns = [
            # Delete/remove timer commands
            (r'\b(delete|remove|clear|cancel|stop|erase|get\s+rid\s+of|kill)\s+(the\s+)?(timer|timers|countdown|countdowns)', 10),
            (r'\b(delete|remove|clear|cancel|stop|erase)\s+(all\s+)?(insulin|correction)\s+(timer|timers|countdown)', 10),
            # All timers patterns
            (r'\b(delete|remove|clear|cancel|stop|erase)\s+all\s+(timer|timers|countdown|countdowns)', 10),
            # Countdown-specific patterns
            (r'\b(delete|remove|clear|cancel|stop|erase)\s+(the\s+)?(countdown|countdowns)', 10),
            # Timer status/info commands
            (r'\b(check|show|what\'s|how\s+long)\s+.*\s+(timer|timers|countdown)', 8),
            (r'\btimer\s+(status|time|left|remaining)\b', 8),
            # Simple "timer" or "countdown" mentions
            (r'\b(timer|countdown)[s]?\b', 5),
        ]

        # Query indicators - asking for information
        self.query_patterns = [
            # Question words at start
            (r'^(what|how|tell|show|give)\s', 3),
            # Nutrition query phrases
            (r'\b(how\s+many|what\'s\s+the|tell\s+me\s+the)\s+(carbs?|calories?|protein|fat|sugar)', 5),
            # Information seeking verbs
            (r'\b(contain|has|have|in\s+a|in\s+an)\b', 2),
            # "Carbs in X" pattern
            (r'\b(carbs?|calories?|protein|fat)\s+in\s+', 4),
            # Nutrition/nutritional info
            (r'\b(nutrition|nutritional)\s+(info|information|facts?)', 5),
        ]

        # Glucose query patterns - these should NOT be treated as food
        self.glucose_patterns = [
            (r'\b(glucose|sugar|blood\s+sugar)\s+(reading|level|number)', 10),
            (r'\bmy\s+(current|latest)?\s*(reading|level|glucose|sugar)', 10),
            (r'what\'s\s+my\s+(glucose|sugar|reading|level)', 10),
            (r'\bcurrent\s+reading\b', 10),
            (r'\bglucose\s+reading\b', 10),
            (r'\bsugar\s+reading\b', 10),
        ]

        # Medical query patterns - asking about doses, levels, etc.
        self.medical_query_patterns = [
            (r'what\'s\s+my\s+\w+\s+(dose|level|amount)', 10),
            (r'\bmy\s+(lantus|humalog|novolog|tresiba|apidra|fiasp|levemir|basaglar)\s+(dose|level|amount)', 10),
            (r'\b(lantus|humalog|novolog|tresiba|apidra|fiasp|levemir|basaglar)\s+(dose|level|amount)', 8),
            (r'\blast\s+dose\s+of\b', 8),
            (r'\bmy\s+last\s+dose\b', 8),
            (r'\bhow\s+much\s+(lantus|humalog|novolog|tresiba|apidra|fiasp|levemir|basaglar)\b', 8),
            (r'\bwhen\s+did\s+i\s+take\b', 8),
            (r'\binsulin\s+(history|log|records?)', 8),
        ]

        # Command indicators - performing actions
        self.command_patterns = [
            # Past tense consumption verbs
            (r'\b(ate|had|consumed|drank|took|finished)\b', 4),
            # Present/future consumption
            (r'\b(eating|having|drinking|taking)\b', 3),
            # Logging verbs
            (r'\b(log|record|track|add|enter|save)\b', 5),
            # Meal type indicators
            (r'\bfor\s+(breakfast|lunch|dinner|snack)\b', 3),
            # Time indicators
            (r'\b(this\s+morning|today|tonight|yesterday|just|now)\b', 2),
            # First person with food
            (r'^i\s+(ate|had|just|am)\s+', 4),
        ]

        # Ambiguous patterns that need context
        self.ambiguous_patterns = [
            # Just food names
            (r'^(apple|banana|pizza|burger|sandwich)s?$', 0),
            # "X carbs" without context
            (r'^\w+\s+carbs?$', 0),
        ]

    def calculate_intent_score(self, command: str) -> Tuple[float, float, float, float]:
        """
        Calculate query, command, timer, and insulin scores for the given input
        Returns: (query_score, command_score, timer_score, insulin_score)
        """
        command_lower = command.lower().strip()

        query_score = 0.0
        command_score = 0.0
        timer_score = 0.0
        insulin_score = 0.0

        # Check medical query patterns first - these should be queries, not insulin commands
        medical_query_found = False
        for pattern, weight in self.medical_query_patterns:
            if re.search(pattern, command_lower):
                query_score += weight
                medical_query_found = True

        # Check insulin patterns - but only if it's not a medical query
        if not medical_query_found:
            for pattern, weight in self.insulin_patterns:
                if re.search(pattern, command_lower):
                    insulin_score += weight

        # Check timer patterns - highest priority
        for pattern, weight in self.timer_patterns:
            if re.search(pattern, command_lower):
                timer_score += weight

        # If this is clearly a timer command, skip other checks
        if timer_score > 0:
            return 0.0, 0.0, 1.0, 0.0

        # Check if this is a glucose query - these should NEVER be food
        for pattern, weight in self.glucose_patterns:
            if re.search(pattern, command_lower):
                # This is definitely NOT a food command
                return 1.0, 0.0, 0.0, 0.0  # 100% query

        # Check query patterns
        for pattern, weight in self.query_patterns:
            if re.search(pattern, command_lower):
                query_score += weight

        # Check command patterns
        for pattern, weight in self.command_patterns:
            if re.search(pattern, command_lower):
                command_score += weight

        # Check for ambiguous patterns
        for pattern, weight in self.ambiguous_patterns:
            if re.search(pattern, command_lower):
                # Ambiguous patterns slightly favor queries
                query_score += 0.5

        # Normalize scores
        total = query_score + command_score + timer_score + insulin_score
        if total > 0:
            query_score = query_score / total
            command_score = command_score / total
            timer_score = timer_score / total
            insulin_score = insulin_score / total

        return query_score, command_score, timer_score, insulin_score

    def classify_intent(self, command: str, confidence_threshold: float = 0.6) -> Dict:
        """
        Classify the intent of a voice command

        Args:
            command: The voice command to classify
            confidence_threshold: Minimum confidence to make a decision

        Returns:
            Dict with 'intent', 'confidence', and 'needs_clarification'
        """
        # Apply STT corrections before classification
        corrected_command = self.stt_processor.process(command)
        if corrected_command != command:
            print(f"[IntentClassifier] Applied STT correction: '{command}' -> '{corrected_command}'")

        # Use the corrected command for scoring
        query_score, command_score, timer_score, insulin_score = self.calculate_intent_score(corrected_command)

        # Determine intent
        scores = [
            ('insulin', insulin_score),
            ('timer', timer_score),
            ('query', query_score),
            ('command', command_score)
        ]
        scores.sort(key=lambda x: x[1], reverse=True)

        intent = scores[0][0]
        confidence = scores[0][1]

        # Check if we need clarification
        needs_clarification = confidence < confidence_threshold

        return {
            'intent': intent,
            'confidence': confidence,
            'needs_clarification': needs_clarification,
            'query_score': query_score,
            'command_score': command_score,
            'timer_score': timer_score,
            'insulin_score': insulin_score
        }

    def is_glucose_query(self, command: str) -> bool:
        """Check if the command is asking about glucose/blood sugar levels"""
        command_lower = command.lower().strip()
        for pattern, _ in self.glucose_patterns:
            if re.search(pattern, command_lower):
                return True
        return False

    def is_timer_command(self, command: str) -> bool:
        """Check if the command is related to timer control"""
        command_lower = command.lower().strip()
        for pattern, _ in self.timer_patterns:
            if re.search(pattern, command_lower):
                return True
        return False

    def is_insulin_command(self, command: str) -> bool:
        """Check if the command is related to insulin logging"""
        command_lower = command.lower().strip()
        for pattern, _ in self.insulin_patterns:
            if re.search(pattern, command_lower):
                return True
        return False

    def contains_non_food_words(self, command: str) -> bool:
        """Check if command contains words that should never be food"""
        words = command.lower().split()
        return any(word in self.non_food_blacklist for word in words)

    def is_definitely_not_food(self, command: str) -> bool:
        """Strong check that this command should NEVER be treated as food"""
        command_lower = command.lower().strip()

        # Check if it's a timer command
        if self.is_timer_command(command_lower):
            return True

        # Check if it contains non-food words
        if self.contains_non_food_words(command_lower):
            return True

        # Check if it matches timer/settings patterns
        if re.search(r'\b(timer|countdown|alarm|reminder|setting)\b', command_lower):
            return True

        # Special check: if command is JUST "insulin" or "correction" alone, block it
        # But allow "X units of insulin" or "took insulin" etc.
        if command_lower in ['insulin', 'correction', 'bolus']:
            return True

        return False

    def get_clarification_prompt(self, command: str) -> str:
        """
        Generate a clarification prompt for ambiguous commands
        """
        # Extract potential food item
        food_match = re.search(r'\b(\w+)(?:\s+carbs?)?$', command.lower())
        food = food_match.group(1) if food_match else "that"

        return f"Did you want me to look up the nutritional information for {food}, or log it as a meal?"
