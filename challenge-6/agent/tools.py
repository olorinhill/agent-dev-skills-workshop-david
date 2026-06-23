"""Tool functions used by the ReadyNow multi-agent system."""

from __future__ import annotations

from typing import Any, Dict, Optional
import os
import time

import requests


GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
WEATHER_URL = "https://weather.googleapis.com/v1/currentConditions:lookup"
DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"


def _maps_api_key() -> str:
    return os.getenv("GOOGLE_MAPS_API_KEY", "").strip()


def _http_get_json(url: str, params: Dict[str, Any], timeout: int = 20) -> Dict[str, Any]:
    """Execute a GET request with basic retries and JSON response parsing."""
    last_error: Optional[Exception] = None
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                return {"error": f"Unexpected response payload type: {type(payload).__name__}"}
            return payload
        except Exception as exc:  # pragma: no cover - defensive for HTTP/runtime differences
            last_error = exc
            if attempt < 2:
                time.sleep(1 + attempt)
    return {"error": f"HTTP request failed: {last_error}"}


def get_lat_lon(place: str) -> Dict[str, Any]:
    """Resolve a location string to latitude and longitude using Google Geocoding."""
    if not place or not place.strip():
        return {"error": "Place must be a non-empty string."}

    api_key = _maps_api_key()
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY is missing."}

    payload = _http_get_json(
        GEOCODE_URL,
        {"address": place.strip(), "key": api_key},
    )
    if payload.get("error"):
        return payload

    if payload.get("status") != "OK":
        return {
            "error": f"Geocoding failed with status={payload.get('status')}",
            "details": payload.get("error_message"),
        }

    results = payload.get("results") or []
    if not results:
        return {"error": f"No geocoding results found for '{place}'."}

    top = results[0]
    geometry = top.get("geometry", {})
    location = geometry.get("location", {})
    if "lat" not in location or "lng" not in location:
        return {"error": "Geocoding response missing coordinates."}

    address_components = top.get("address_components") or []
    country = ""
    for component in address_components:
        types = component.get("types") or []
        if "country" in types:
            country = component.get("short_name", "")
            break

    return {
        "resolved_place": top.get("formatted_address", place.strip()),
        "country_code": country,
        "lat": float(location["lat"]),
        "lon": float(location["lng"]),
    }


def get_weather_forecast(lat: float, lon: float) -> Dict[str, Any]:
    """Retrieve current weather conditions from the Google Weather API."""
    api_key = _maps_api_key()
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY is missing."}

    payload = _http_get_json(
        WEATHER_URL,
        {
            "key": api_key,
            "location.latitude": lat,
            "location.longitude": lon,
            "unitsSystem": "IMPERIAL",
        },
    )
    if payload.get("error"):
        return payload

    condition = payload.get("weatherCondition", {})
    temp = payload.get("temperature", {})
    feels_like = payload.get("feelsLikeTemperature", {})
    precip = payload.get("precipitation", {})
    wind = payload.get("wind", {})

    alerts = []
    if (precip.get("probability", {}).get("percent", 0) or 0) >= 70:
        alerts.append("High precipitation probability")
    if (wind.get("speed", {}).get("value", 0) or 0) >= 30:
        alerts.append("Strong wind conditions")
    if (temp.get("degrees", 70) or 70) <= 32:
        alerts.append("Freezing temperature risk")
    if (temp.get("degrees", 70) or 70) >= 100:
        alerts.append("Extreme heat risk")

    return {
        "summary": condition.get("description", {}).get("text", "No condition summary available."),
        "temperature_f": temp.get("degrees"),
        "feels_like_f": feels_like.get("degrees"),
        "humidity_pct": payload.get("relativeHumidity"),
        "precipitation_probability_pct": precip.get("probability", {}).get("percent"),
        "wind_speed_mph": wind.get("speed", {}).get("value"),
        "alerts": alerts,
    }


def get_evacuation_route(
    origin: str,
    destination: str,
    mode: str = "driving",
) -> Dict[str, Any]:
    """Retrieve an evacuation route summary between origin and destination."""
    if not origin.strip() or not destination.strip():
        return {"error": "Both origin and destination are required."}

    api_key = _maps_api_key()
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY is missing."}

    payload = _http_get_json(
        DIRECTIONS_URL,
        {
            "origin": origin.strip(),
            "destination": destination.strip(),
            "mode": mode.strip().lower() or "driving",
            "alternatives": "true",
            "key": api_key,
        },
    )
    if payload.get("error"):
        return payload

    if payload.get("status") != "OK":
        return {
            "error": f"Directions lookup failed with status={payload.get('status')}",
            "details": payload.get("error_message"),
        }

    routes = payload.get("routes") or []
    if not routes:
        return {"error": "No routes available for the requested trip."}

    best = routes[0]
    legs = best.get("legs") or []
    if not legs:
        return {"error": "Directions response missing leg data."}

    leg = legs[0]
    step_instructions = []
    for step in leg.get("steps", [])[:5]:
        html_instr = step.get("html_instructions", "")
        # Keep output concise and safe for plain text channels.
        instruction = (
            html_instr.replace("<b>", "")
            .replace("</b>", "")
            .replace("<div style=\"font-size:0.9em\">", " ")
            .replace("</div>", "")
        )
        step_instructions.append(instruction)

    alternative_count = max(0, len(routes) - 1)
    return {
        "origin": leg.get("start_address", origin),
        "destination": leg.get("end_address", destination),
        "distance": leg.get("distance", {}).get("text"),
        "duration": leg.get("duration", {}).get("text"),
        "start_location": leg.get("start_location"),
        "end_location": leg.get("end_location"),
        "top_steps": step_instructions,
        "alternative_routes_available": alternative_count,
    }
