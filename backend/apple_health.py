import xml.etree.ElementTree as ET
import zipfile
import io
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Maps Apple Health HKQuantityType identifiers to our internal metric names
METRIC_MAPPINGS = {
    "HKQuantityTypeIdentifierStepCount": ("steps", "count"),
    "HKQuantityTypeIdentifierActiveEnergyBurned": ("active_calories", "kcal"),
    "HKQuantityTypeIdentifierRestingHeartRate": ("resting_heart_rate", "bpm"),
    "HKQuantityTypeIdentifierHeartRate": ("heart_rate", "bpm"),
    "HKQuantityTypeIdentifierVO2Max": ("vo2_max", "ml/kg/min"),
    "HKQuantityTypeIdentifierBodyMass": ("body_weight", "kg"),
    "HKQuantityTypeIdentifierAppleExerciseTime": ("exercise_minutes", "min"),
    "HKQuantityTypeIdentifierAppleStandTime": ("stand_minutes", "min"),
    "HKQuantityTypeIdentifierDistanceWalkingRunning": ("distance_km", "km"),
    "HKQuantityTypeIdentifierFlightsClimbed": ("flights_climbed", "count"),
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN": ("hrv", "ms"),
    "HKQuantityTypeIdentifierRespiratoryRate": ("respiratory_rate", "breaths/min"),
    "HKQuantityTypeIdentifierOxygenSaturation": ("spo2", "%"),
    "HKQuantityTypeIdentifierBodyFatPercentage": ("body_fat", "%"),
    "HKQuantityTypeIdentifierLeanBodyMass": ("lean_body_mass", "kg"),
    "HKQuantityTypeIdentifierDietaryEnergyConsumed": ("calories_consumed", "kcal"),
    "HKQuantityTypeIdentifierDietaryProtein": ("protein_g", "g"),
    "HKQuantityTypeIdentifierDietaryCarbohydrates": ("carbs_g", "g"),
    "HKQuantityTypeIdentifierDietaryFatTotal": ("fat_g", "g"),
}

# Metrics that should be summed per day vs averaged
SUM_METRICS = {
    "steps", "active_calories", "exercise_minutes", "stand_minutes",
    "distance_km", "flights_climbed", "calories_consumed",
    "protein_g", "carbs_g", "fat_g",
}


def parse_apple_health_export(file_content: bytes, filename: str) -> List[Dict[str, Any]]:
    """Parse Apple Health export (export.xml or export.zip) into metric records."""
    try:
        if filename.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(file_content)) as z:
                xml_files = [f for f in z.namelist() if f.endswith(".xml") and "export" in f.lower()]
                if not xml_files:
                    xml_files = [f for f in z.namelist() if f.endswith(".xml")]
                if not xml_files:
                    logger.error("No XML file found in ZIP")
                    return []
                xml_content = z.read(xml_files[0])
        else:
            xml_content = file_content

        return _parse_xml(xml_content)
    except Exception as e:
        logger.error(f"Apple Health parse error: {e}")
        return []


def _parse_xml(xml_content: bytes) -> List[Dict[str, Any]]:
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return []

    # daily_data[date][metric] = list of values
    daily_data: Dict[str, Dict[str, List[float]]] = {}

    for record in root.findall("Record"):
        record_type = record.get("type", "")
        mapping = METRIC_MAPPINGS.get(record_type)
        if not mapping:
            continue

        metric_name, _ = mapping
        date_str = (record.get("startDate") or "")[:10]
        if not date_str:
            continue

        try:
            value = float(record.get("value", 0))
        except (ValueError, TypeError):
            continue

        if date_str not in daily_data:
            daily_data[date_str] = {}
        if metric_name not in daily_data[date_str]:
            daily_data[date_str][metric_name] = []
        daily_data[date_str][metric_name].append(value)

    # Parse workouts
    for workout in root.findall("Workout"):
        date_str = (workout.get("startDate") or "")[:10]
        if not date_str:
            continue

        try:
            duration_min = float(workout.get("duration") or 0)
            calories = float(workout.get("totalEnergyBurned") or 0)

            if date_str not in daily_data:
                daily_data[date_str] = {}

            if "workout_minutes" not in daily_data[date_str]:
                daily_data[date_str]["workout_minutes"] = []
            daily_data[date_str]["workout_minutes"].append(duration_min)

            if calories > 0:
                if "workout_calories" not in daily_data[date_str]:
                    daily_data[date_str]["workout_calories"] = []
                daily_data[date_str]["workout_calories"].append(calories)
        except (ValueError, TypeError):
            continue

    # Aggregate and build output
    metrics: List[Dict[str, Any]] = []
    for date_str, metrics_dict in daily_data.items():
        for metric_name, values in metrics_dict.items():
            if not values:
                continue

            # Determine unit
            unit = _get_unit(metric_name)

            # Sum or average depending on metric type
            if metric_name in SUM_METRICS or metric_name in ("workout_minutes", "workout_calories"):
                value = sum(values)
            else:
                value = sum(values) / len(values)

            metrics.append({
                "date": date_str,
                "metric_type": metric_name,
                "value": round(value, 2),
                "unit": unit,
                "source": "apple_health",
            })

    logger.info(f"Parsed {len(metrics)} metrics from Apple Health export")
    return metrics


def _get_unit(metric_name: str) -> str:
    unit_map = {
        "steps": "count",
        "active_calories": "kcal",
        "resting_heart_rate": "bpm",
        "heart_rate": "bpm",
        "vo2_max": "ml/kg/min",
        "body_weight": "kg",
        "exercise_minutes": "min",
        "stand_minutes": "min",
        "distance_km": "km",
        "flights_climbed": "count",
        "hrv": "ms",
        "respiratory_rate": "breaths/min",
        "spo2": "%",
        "body_fat": "%",
        "lean_body_mass": "kg",
        "calories_consumed": "kcal",
        "protein_g": "g",
        "carbs_g": "g",
        "fat_g": "g",
        "workout_minutes": "min",
        "workout_calories": "kcal",
    }
    return unit_map.get(metric_name, "")
