"""
Timer command parser.
Handles voice commands for stopping/deleting insulin timers.
"""
import re
import logging

logger = logging.getLogger("diabeetech.voice.parsers.timer")

# Stop/delete patterns
STOP_PATTERNS = re.compile(
    r'(?:stop|cancel|end|clear|delete|remove|erase|kill)\s+'
    r'(?:the\s+)?'
    r'(?:(?P<target>all|correction|primary)\s+)?'
    r'(?:insulin\s+)?'
    r'(?:timer|countdown|timers)',
    re.IGNORECASE
)

# Specific timer by number: "delete timer 1", "delete the first timer"
SPECIFIC_NUMBER_PATTERN = re.compile(
    r'(?:stop|cancel|delete|remove)\s+(?:the\s+)?'
    r'(?:(?P<ordinal>first|second|1st|2nd|1|2)\s+)?'
    r'(?:insulin\s+)?timer',
    re.IGNORECASE
)

# Specific timer by units: "delete the 6 unit timer"
SPECIFIC_UNITS_PATTERN = re.compile(
    r'(?:stop|cancel|delete|remove)\s+(?:the\s+)?'
    r'(?P<units>\d+(?:\.\d+)?)\s*'
    r'(?:unit|u)\s*(?:insulin\s+)?timer',
    re.IGNORECASE
)


def parse_timer_command(text: str) -> dict | None:
    """
    Parse a timer stop/delete command from text.

    Returns:
        dict with keys:
            action: "stop"
            target: "all" | "correction" | "primary" | "specific"
            data: optional dict with timer_number or units
        None if not a timer command
    """
    text = text.strip().lower()

    # Check for specific timer by units
    match = SPECIFIC_UNITS_PATTERN.search(text)
    if match:
        return {
            "action": "stop",
            "target": "specific",
            "data": {"units": float(match.group("units"))}
        }

    # Check for specific timer by number
    match = SPECIFIC_NUMBER_PATTERN.search(text)
    if match:
        ordinal = match.group("ordinal")
        if ordinal:
            ordinal_map = {"first": 1, "1st": 1, "1": 1, "second": 2, "2nd": 2, "2": 2}
            timer_number = ordinal_map.get(ordinal, 1)
            return {
                "action": "stop",
                "target": "specific",
                "data": {"timer_number": timer_number}
            }

    # Check for general stop command
    match = STOP_PATTERNS.search(text)
    if match:
        target = match.group("target") or "all"
        return {
            "action": "stop",
            "target": target.lower(),
            "data": {}
        }

    return None
