"""
Glucose Command Parser for Voice Assistant
Handles glucose query voice commands (current / historical)

Migrated from itiflux voice_assistant/command_parser.py
- Removed PyQt5 dependencies
- All regex patterns and day-part defaults preserved verbatim
"""

import re
from datetime import datetime, timedelta

# Day-part defaults
DAY_PART_DEFAULTS = {
    "morning": (9, 0),
    "afternoon": (13, 0),
    "evening": (19, 0)
}


class GlucoseCommandParser:
    @staticmethod
    def parse(command: str):
        """
        Parse the user command and return a dict with:
          - 'intent': 'current' or 'historical' or 'unknown'
          - 'time': datetime for historical queries, else None
        """
        cmd = command.strip().lower()
        if GlucoseCommandParser._is_current_query(cmd):
            return {'intent': 'current', 'time': None}

        dt = GlucoseCommandParser._parse_time(cmd)
        if dt:
            return {'intent': 'historical', 'time': dt}

        return {'intent': 'unknown', 'time': None}

    @staticmethod
    def _is_current_query(cmd: str) -> bool:
        patterns = [
            r"\b(current|latest|now)\b.*\b(glucose|sugar|level)\b",
            r"\b(glucose|sugar|level)\b.*\b(current|now|latest)\b",
            r"\b(what(?:'s| is))\b.*\b(glucose|sugar|level)\b",
            r"^\s*(?:glucose|sugar|level)\s*$"   # catch one-word queries like "level"
        ]
        return any(re.search(p, cmd) for p in patterns)

    @staticmethod
    def _parse_time(cmd: str):
        now = datetime.now()

        # "yesterday [at <time|noon|midnight|part>]"
        m = re.search(
            r"\byesterday"
            r"(?:\s+(?:at\s+)?"
            r"(?P<time>"
            r"\d{1,2}(?::\d{2})?\s*(?:am|pm)"
            r"|noon|midnight"
            r"|morning|afternoon|evening"
            r")"
            r")?",
            cmd
        )
        if m:
            base = now - timedelta(days=1)
            return GlucoseCommandParser._extract_time(m.group('time'), base)

        # "<N> days|weeks ago [at <time|...>]"
        m = re.search(
            r"(?P<num>\d+)\s+(?P<unit>days?|weeks?)\s+ago"
            r"(?:\s+(?:at\s+)?"
            r"(?P<time>"
            r"\d{1,2}(?::\d{2})?\s*(?:am|pm)"
            r"|noon|midnight"
            r"|morning|afternoon|evening"
            r")"
            r")?",
            cmd
        )
        if m:
            num, unit = int(m.group('num')), m.group('unit')
            delta = timedelta(days=num) if 'day' in unit else timedelta(weeks=num)
            base = now - delta
            return GlucoseCommandParser._extract_time(m.group('time'), base)

        return None

    @staticmethod
    def _extract_time(token: str, base: datetime):
        base = base.replace(second=0, microsecond=0)
        if not token:
            return base

        t = token.strip()
        if t == 'noon':
            return base.replace(hour=12, minute=0)
        if t == 'midnight':
            return base.replace(hour=0, minute=0)
        if t in DAY_PART_DEFAULTS:
            h, m = DAY_PART_DEFAULTS[t]
            return base.replace(hour=h, minute=m)

        # parse "hh[:mm] am/pm"
        m = re.match(r"(?P<h>\d{1,2})(?::(?P<mi>\d{2}))?\s*(?P<ap>am|pm)", t)
        if m:
            h = int(m.group('h'))
            mi = int(m.group('mi') or 0)
            ap = m.group('ap')
            if ap == 'pm' and h != 12:
                h += 12
            if ap == 'am' and h == 12:
                h = 0
            return base.replace(hour=h, minute=mi)

        return base
