"""
Clarity analytics — glucose statistics calculations.
Provides GMI, Time in Range, standard deviation, coefficient of variation.
"""
import json
import logging
import math
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("diabeetech.clarity")

CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"


def calculate_gmi(average_glucose: float) -> float:
    """GMI = 3.31 + (0.02392 x mean glucose in mg/dL)"""
    return round(3.31 + (0.02392 * average_glucose), 1)


def calculate_time_in_range(readings: list, thresholds: dict) -> dict:
    """
    Calculate time in range percentages.
    very_high: sgv > 250
    high: sgv > threshold_high AND sgv <= 250
    in_range: sgv >= threshold_low AND sgv <= threshold_trending_high
    low: sgv >= 54 AND sgv < threshold_low
    very_low: sgv < 54
    """
    total = len(readings)
    if total == 0:
        return {k: 0.0 for k in ["very_high", "high", "in_range", "low", "very_low"]}

    th_high = thresholds.get("threshold_high", 300)
    th_low = thresholds.get("threshold_low", 100)
    th_trending_high = thresholds.get("threshold_trending_high", 263)

    counts = {"very_high": 0, "high": 0, "in_range": 0, "low": 0, "very_low": 0}
    for r in readings:
        sgv = r if isinstance(r, (int, float)) else r.get("sgv", 0)
        if sgv > 250:
            counts["very_high"] += 1
        elif sgv > th_high:
            counts["high"] += 1
        elif sgv >= th_low:
            counts["in_range"] += 1
        elif sgv >= 54:
            counts["low"] += 1
        else:
            counts["very_low"] += 1

    return {k: round((v / total) * 100, 1) for k, v in counts.items()}


def calculate_cv(readings: list) -> float:
    """Coefficient of Variation = (std_dev / mean) x 100"""
    values = [r if isinstance(r, (int, float)) else r.get("sgv", 0) for r in readings]
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    if mean == 0:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std_dev = math.sqrt(variance)
    return round((std_dev / mean) * 100, 1)


def get_clarity_stats(period_days: int = 7, thresholds: Optional[dict] = None) -> dict:
    """Calculate all clarity statistics for the given period."""
    if thresholds is None:
        thresholds = {
            "threshold_high": 300,
            "threshold_trending_high": 263,
            "threshold_trending_low": 120,
            "threshold_low": 100,
        }

    # Load cached historical data
    cache_path = CACHE_DIR / "historical_data.json"
    if not cache_path.exists():
        return _empty_stats(period_days)

    try:
        all_readings = json.loads(cache_path.read_text())
    except Exception:
        return _empty_stats(period_days)

    if not all_readings:
        return _empty_stats(period_days)

    # Filter to period
    cutoff = datetime.now() - timedelta(days=period_days)
    cutoff_ms = cutoff.timestamp() * 1000

    period_readings = []
    for r in all_readings:
        ts = r.get("date") or r.get("mills", 0)
        if ts > cutoff_ms:
            period_readings.append(r)

    if not period_readings:
        return _empty_stats(period_days)

    # Extract sgv values
    sgv_values = [r.get("sgv", 0) for r in period_readings if r.get("sgv")]
    if not sgv_values:
        return _empty_stats(period_days)

    # Calculate stats
    avg = sum(sgv_values) / len(sgv_values)
    variance = sum((v - avg) ** 2 for v in sgv_values) / len(sgv_values)
    std_dev = math.sqrt(variance)
    gmi = calculate_gmi(avg)
    tir = calculate_time_in_range(sgv_values, thresholds)
    cv = calculate_cv(sgv_values)

    # Expected readings (1 every 5 min)
    expected = period_days * 24 * 12  # 288 per day
    data_sufficiency = round((len(sgv_values) / expected) * 100, 1) if expected > 0 else 0

    # Prior period comparison
    prior_cutoff_ms = (cutoff - timedelta(days=period_days)).timestamp() * 1000
    prior_readings = [r for r in all_readings if cutoff_ms > (r.get("date") or r.get("mills", 0)) > prior_cutoff_ms]
    prior_sgv = [r.get("sgv", 0) for r in prior_readings if r.get("sgv")]
    prior_avg = sum(prior_sgv) / len(prior_sgv) if prior_sgv else avg

    avg_change = round(avg - prior_avg, 1)
    avg_change_pct = round(((avg - prior_avg) / prior_avg) * 100, 1) if prior_avg else 0

    return {
        "period_days": period_days,
        "total_readings": len(sgv_values),
        "average_glucose": round(avg, 1),
        "std_deviation": round(std_dev, 1),
        "gmi": gmi,
        "time_in_range": tir,
        "coefficient_of_variation": cv,
        "data_sufficiency": min(data_sufficiency, 100.0),
        "vs_prior_period": {
            "average_change": avg_change,
            "average_change_pct": avg_change_pct,
        },
    }


def _empty_stats(period_days: int) -> dict:
    return {
        "period_days": period_days,
        "total_readings": 0,
        "average_glucose": 0,
        "std_deviation": 0,
        "gmi": 0,
        "time_in_range": {"very_high": 0, "high": 0, "in_range": 0, "low": 0, "very_low": 0},
        "coefficient_of_variation": 0,
        "data_sufficiency": 0,
        "vs_prior_period": {"average_change": 0, "average_change_pct": 0},
    }
