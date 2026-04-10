# Pollution Index Tool

import logging
import re
import requests
from difflib import get_close_matches
from typing import Dict, Optional, Tuple
from datetime import datetime
try:
    from utils.location_disambiguation import format_ambiguity_prompt, get_city_ambiguity_description
except ImportError:
    from src.utils.location_disambiguation import format_ambiguity_prompt, get_city_ambiguity_description

logger = logging.getLogger("GreenMind")

class PollutionIndexTool:
    """
    Tool to get pollution and air quality information for various locations
    """
    
    def __init__(self):
        self.name = "pollution_index"
        self.description = "Get current pollution and air quality data for countries, states, and cities"
        
        # Sample air quality data (in real implementation, would call API)
        self.air_quality_data = {
            "India": {
                "Delhi": {"aqi": 285, "level": "Very Poor", "pm25": 178, "forecast": "Improve to Poor in 2-3 days"},
                "Mumbai": {"aqi": 165, "level": "Unhealthy", "pm25": 92, "forecast": "Maintain at Unhealthy levels"},
                "Bangalore": {"aqi": 85, "level": "Moderate", "pm25": 42, "forecast": "Improve to Good in 3 days"},
                "Hyderabad": {"aqi": 102, "level": "Moderate", "pm25": 50, "forecast": "Stable Moderate"}
            },
            "USA": {
                "Los Angeles": {"aqi": 145, "level": "Unhealthy for Sensitive Groups", "pm25": 65, "forecast": "Improve with wind patterns"},
                "New York": {"aqi": 68, "level": "Moderate", "pm25": 35, "forecast": "Good air quality expected"},
                "Chicago": {"aqi": 78, "level": "Moderate", "pm25": 38, "forecast": "Stable Moderate, slight improvement expected"},
                "Houston": {"aqi": 112, "level": "Unhealthy for Sensitive Groups", "pm25": 55, "forecast": "Industrial activity may sustain current levels"},
                "Phoenix": {"aqi": 125, "level": "Unhealthy for Sensitive Groups", "pm25": 60, "forecast": "Dust events may worsen conditions temporarily"},
                "San Francisco": {"aqi": 52, "level": "Moderate", "pm25": 26, "forecast": "Improve to Good with ocean breeze"},
                "Seattle": {"aqi": 45, "level": "Good", "pm25": 20, "forecast": "Remain Good; wildfire season may cause spikes"},
                "Denver": {"aqi": 88, "level": "Moderate", "pm25": 44, "forecast": "Stable; ozone may rise in summer months"},
                "Miami": {"aqi": 58, "level": "Moderate", "pm25": 29, "forecast": "Good conditions expected with sea breeze"},
                "Atlanta": {"aqi": 95, "level": "Moderate", "pm25": 47, "forecast": "Stable Moderate"},
                "Boston": {"aqi": 62, "level": "Moderate", "pm25": 31, "forecast": "Improve to Good by weekend"},
                "Portland": {"aqi": 48, "level": "Good", "pm25": 22, "forecast": "Good; wildfire smoke risk in summer"},
                "Vancouver": {"aqi": 70, "level": "Moderate", "pm25": 33, "forecast": "Stable Moderate"},
                "Arlington": {"aqi": 74, "level": "Moderate", "pm25": 36, "forecast": "Likely to remain Moderate"},
                "Dublin": {"aqi": 72, "level": "Moderate", "pm25": 34, "forecast": "Stable with minor improvements expected"},
            },
            "Canada": {
                "Vancouver": {"aqi": 60, "level": "Good", "pm25": 28, "forecast": "Remains Good"}
            },
            "China": {
                "Beijing": {"aqi": 195, "level": "Unhealthy", "pm25": 110, "forecast": "Worsen with industry activity"},
                "Shanghai": {"aqi": 92, "level": "Moderate", "pm25": 48, "forecast": "Maintain Moderate levels"}
            },
            "UK": {
                "London": {"aqi": 55, "level": "Good", "pm25": 28, "forecast": "Remain Good"}
            },
            "Ireland": {
                "Dublin": {"aqi": 58, "level": "Moderate", "pm25": 30, "forecast": "Good conditions expected"}
            }
        }

        self._us_aliases = {
            "us", "usa", "u.s.", "u.s.a.", "united states", "united states of america"
        }
        self._us_state_codes = {
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
            "DC"
        }

    def _aqi_level(self, aqi: int) -> str:
        if aqi <= 50:
            return "Good"
        if aqi <= 100:
            return "Moderate"
        if aqi <= 150:
            return "Unhealthy for Sensitive Groups"
        if aqi <= 200:
            return "Unhealthy"
        if aqi <= 300:
            return "Very Unhealthy"
        return "Hazardous"

    def _is_usa_context(self, parts) -> bool:
        if not parts:
            return False

        lowered_parts = [p.strip().lower() for p in parts if p.strip()]
        if any(p in self._us_aliases for p in lowered_parts):
            return True

        # Accept common "City, ST" format like "Seattle, WA"
        if len(parts) >= 2 and parts[1].strip().upper() in self._us_state_codes:
            return True

        return False

    def _resolve_us_city(self, location: str) -> Optional[Tuple[str, float, float, str]]:
        """Resolve any US city using Open-Meteo geocoding API."""
        try:
            query = location.strip()
            if not query:
                return None

            url = "https://geocoding-api.open-meteo.com/v1/search"
            params = {
                "name": query,
                "count": 8,
                "language": "en",
                "format": "json",
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json() or {}
            results = data.get("results", [])
            if not results:
                return None

            us_result = None
            for r in results:
                country_code = (r.get("country_code") or "").upper()
                country = (r.get("country") or "")
                if country_code == "US" or country == "United States":
                    us_result = r
                    break

            if not us_result:
                return None

            city = us_result.get("name", "Unknown")
            admin = us_result.get("admin1", "USA")
            lat = us_result.get("latitude")
            lon = us_result.get("longitude")
            if lat is None or lon is None:
                return None

            return city, float(lat), float(lon), admin
        except Exception as e:
            logger.warning(f"Unable to resolve US city '{location}' via geocoding API: {e}")
            return None

    def _fetch_live_air_quality(self, city: str, latitude: float, longitude: float) -> Optional[Dict]:
        """Fetch live AQI and PM2.5 from Open-Meteo air quality API."""
        try:
            url = "https://air-quality-api.open-meteo.com/v1/air-quality"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "hourly": "us_aqi,pm2_5",
                "timezone": "auto",
                "forecast_days": 1,
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json() or {}
            hourly = data.get("hourly", {})
            aqi_series = hourly.get("us_aqi", []) or []
            pm25_series = hourly.get("pm2_5", []) or []

            # Use latest non-null values
            latest_aqi = next((v for v in reversed(aqi_series) if v is not None), None)
            latest_pm25 = next((v for v in reversed(pm25_series) if v is not None), None)

            if latest_aqi is None:
                return None

            aqi_value = int(round(float(latest_aqi)))
            pm25_value = round(float(latest_pm25), 1) if latest_pm25 is not None else "N/A"
            level = self._aqi_level(aqi_value)

            forecast_text = "Short-term conditions may vary with traffic, weather, and wildfire smoke patterns."
            return {
                "aqi": aqi_value,
                "pm25": pm25_value,
                "level": level,
                "forecast": forecast_text,
                "source": "Open-Meteo Air Quality API",
            }
        except Exception as e:
            logger.warning(f"Unable to fetch live air quality for '{city}': {e}")
            return None

    def _build_us_longterm_projection(self, baseline_aqi: int) -> Dict:
        """Create 2026-2035 projection for any US city not in curated forecast data."""
        if baseline_aqi <= 50:
            annual_improvement = 0.7
        elif baseline_aqi <= 100:
            annual_improvement = 1.2
        elif baseline_aqi <= 150:
            annual_improvement = 1.8
        elif baseline_aqi <= 200:
            annual_improvement = 2.5
        else:
            annual_improvement = 3.5

        projections = {}
        for year in range(2026, 2036):
            offset = year - 2026
            projected = max(15, int(round(baseline_aqi - (annual_improvement * offset))))
            projections[year] = projected

        return {
            "trend": "improving",
            "driver": "EPA standards, state clean-air plans, and transport electrification trends",
            "projections": projections,
        }
    
    def get_air_quality(self, location: str) -> str:
        """
        Get air quality data for a specific location
        
        Args:
            location: City/country name
        
        Returns:
            Formatted air quality report
        """
        
        # Validate input
        if not location or not isinstance(location, str):
            return "Error: Location must be a non-empty string."
        
        # Limit location length to prevent abuse
        max_location_length = 200
        if len(location) > max_location_length:
            location = location[:max_location_length]
        
        # Normalize location input by removing punctuation and extra spaces
        location_clean = re.sub(r"[^A-Za-z\s,]", "", location or "").strip()
        if not location_clean:
            return "I don't know the current air quality for that location. Please provide a valid city name."

        parts = [p.strip() for p in location_clean.split(',') if p.strip()]
        city_query = parts[0].title() if parts else ""
        region_query = None
        country_query = None
        usa_context = self._is_usa_context(parts)

        # Handle conversational suffixes like "Seattle today" or "Houston right now"
        # so callers don't need perfect location formatting.
        if city_query:
            city_query = re.sub(
                r"\b(today|now|currently|right now|at the moment|tonight|this morning|this evening|please)\b",
                "",
                city_query,
                flags=re.IGNORECASE,
            )
            city_query = re.sub(r"\s+", " ", city_query).strip().title()

        if not city_query:
            return "I don't know the current air quality for that location. Please provide a valid city name."

        if len(parts) == 2:
            region_query = parts[1].title()
        elif len(parts) >= 3:
            region_query = parts[1].title()  # state or region
            country_query = parts[-1].title()

            if country_query in ["Us", "Usa", "United States", "United States Of America", "U.S.A."]:
                country_query = "USA"
            if region_query == "Ca":
                country_query = "USA"

        if country_query:
            region_query = country_query

        # If user specifies country/region explicitly, prioritize that
        if region_query:
            # Country direct
            for country, cities in self.air_quality_data.items():
                if region_query == country:
                    if city_query in cities:
                        return self._format_city_report(city_query, cities[city_query])
                    # Return country summary only when user explicitly asks for the country,
                    # not when they asked for a specific city within that country.
                    if city_query == country or len(parts) == 1:
                        return self._format_country_report(country, cities)
                    break

            # State or city variant match in a specific country
            for country, cities in self.air_quality_data.items():
                if region_query in cities:
                    if city_query in cities:
                        return self._format_city_report(city_query, cities[city_query])

        # If location is a country
        for country, cities in self.air_quality_data.items():
            if city_query == country:
                return self._format_country_report(country, cities)

        # Find all city matches across available country data
        matches = []
        for country, cities in self.air_quality_data.items():
            if city_query in cities:
                matches.append((country, city_query, cities[city_query]))

        if len(matches) == 1:
            country, city, data = matches[0]
            return self._format_city_report(city, data)

        if len(matches) > 1:
            regions = {country for country, _, _ in matches}
            return format_ambiguity_prompt(city_query, regions)

        desc = get_city_ambiguity_description(city_query)
        if desc:
            return (
                f"The city '{city_query}' may refer to multiple areas ({desc}). "
                "Please specify city, state, and country (e.g., 'Kansas City, Missouri, USA')."
            )

        # Fuzzy match city names to handle typos (e.g., Bellevue/Belluvue)
        known_cities = [city for cities in self.air_quality_data.values() for city in cities]
        close_matches = get_close_matches(city_query, known_cities, n=1, cutoff=0.7)
        if close_matches:
            best_city = close_matches[0]
            for country, cities in self.air_quality_data.items():
                if best_city in cities:
                    logger.info(f"Using close match city '{best_city}' for input '{city_query}'")
                    return self._format_city_report(best_city, cities[best_city])

        # Dynamic support for any US city via live APIs
        us_resolution_query = city_query if usa_context and city_query else f"{city_query}, USA"
        resolved = self._resolve_us_city(us_resolution_query)
        if resolved:
            resolved_city, lat, lon, admin = resolved
            live_data = self._fetch_live_air_quality(resolved_city, lat, lon)
            if live_data:
                logger.info(f"Using live US air quality data for '{resolved_city}, {admin}'")
                return self._format_city_report(f"{resolved_city}, {admin}", live_data)

        logger.warning(f"Air quality data not found for '{location}'. Unable to provide current data.")

        # If user asked about weather specifically, provide clear fallback
        if any(term in location.lower() for term in ["weather", "temperature"]):
            return "I don't know the current weather for that location. This system provides air quality and environmental health insights, not live weather forecasts."

        return self._get_available_cities_message(location)    
    def _format_city_report(self, city: str, data: Dict) -> str:
        """Format air quality report for a city"""
        
        aqi = data.get('aqi', 'N/A')
        level = data.get('level', 'Unknown')
        pm25 = data.get('pm25', 'N/A')
        forecast = data.get('forecast', 'No forecast available')
        
        report = f"""
Air Quality Report for {city}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Current Air Quality Index (AQI): {aqi}
Air Quality Level: {level}
PM2.5 Concentration: {pm25} µg/m³

Health Recommendations:
"""
        
        # Add health recommendations based on AQI level
        health_recommendations = {
            "Good": "- Air pollution poses little to no risk. Outdoor activities are safe.",
            "Moderate": "- Air pollution is acceptable. However, some sensitive groups should limit outdoor activity.",
            "Unhealthy for Sensitive Groups": "- Sensitive groups: limit prolonged outdoor activity.\n- General public: outdoor activity is generally safe.",
            "Unhealthy": "- Sensitive groups: avoid prolonged outdoor activity.\n- General public: limit intense outdoor activity.",
            "Very Unhealthy": "- Everyone should avoid prolonged outdoor activity.",
            "Hazardous": "- Everyone should avoid all outdoor activity."
        }
        
        recommendation = health_recommendations.get(level, "Check local health guidelines")
        report += recommendation
        
        report += f"\n\nForecast: {forecast}"
        
        return report
    
    def _get_available_cities_message(self, query: str) -> str:
        """Generate a message showing all available countries and cities for air quality data"""
        message = f"Sorry, I'm not trained on '{query}'.\n\n"
        message += "I support any USA city using live data.\n"
        message += "For non-USA locations, here are the countries and cities I have curated data for:\n\n"
        
        for country, cities in self.air_quality_data.items():
            city_list = ', '.join(sorted(cities.keys()))
            message += f"• {country}: {city_list}\n"
        
        message += "\nTry 'City, State, USA' for US locations (e.g., 'Seattle, WA, USA')."
        message += " For other countries, select a city from the list above (e.g., 'Dublin, Ireland')."
        return message
    
    def _format_country_report(self, country: str, cities: Dict) -> str:
        """Format air quality report for a country"""
        
        report = f"""
Air Quality Report for {country}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

City-wise Air Quality:
"""
        
        for city, data in cities.items():
            aqi = data.get('aqi', 'N/A')
            level = data.get('level', 'Unknown')
            report += f"\n  {city}: AQI {aqi} ({level})"
        
        return report
    
    def _generate_simulated_report(self, location: str) -> str:
        """Generate simulated air quality data for unknown locations"""
        
        report = f"""
Air Quality Report for {location}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Based on global averages for similar regions:

Current Air Quality Index (AQI): 95
Air Quality Level: Moderate
PM2.5 Concentration: 48 µg/m³

Health Recommendations:
- Air pollution is acceptable
- Sensitive groups should consider limiting prolonged outdoor activity
- General public: outdoor activities are generally fine

Forecast: 
- Expected to remain at Moderate levels for the next 5 days
- Favorable weather patterns may improve conditions

Suggestions:
- Monitor local air quality regularly
- Use air purifiers indoors if needed
- Wear N95 masks during high pollution episodes
"""
        
        return report
    
    def get_pollution_forecast(self, location: str, days: int = 7) -> str:
        """
        Get pollution forecast for future days
        
        Args:
            location: City/country name
            days: Number of days to forecast
        
        Returns:
            Forecast report
        """
        report = f"""
Air Quality Forecast for {location} ({days}-day forecast)

Day-by-day expectation:
- Days 1-2: Stable conditions
- Days 3-5: Improving trends
- Days 6-7: Variable conditions

Overall Trend: Mixed conditions expected
"""
        return report

    def get_longterm_forecast(self, location: str) -> str:
        """
        Get long-term yearly AQI projections (2026-2035) for a location.

        Args:
            location: City, state, or country name

        Returns:
            Formatted multi-year forecast report
        """
        # Yearly AQI trend projections per location (2026-2035)
        longterm_data = {
            "India": {
                "Delhi": {
                    "trend": "improving",
                    "driver": "NCAP targets, EV adoption, coal phase-down",
                    "projections": {2026: 270, 2027: 250, 2028: 230, 2029: 210, 2030: 190, 2031: 175, 2032: 160, 2033: 148, 2034: 135, 2035: 122}
                },
                "Mumbai": {
                    "trend": "improving",
                    "driver": "Industrial emission controls, clean fuel transition",
                    "projections": {2026: 155, 2027: 145, 2028: 132, 2029: 120, 2030: 108, 2031: 98, 2032: 90, 2033: 82, 2034: 76, 2035: 70}
                },
                "Bangalore": {
                    "trend": "stable",
                    "driver": "Tech-sector green initiatives; traffic growth offsetting gains",
                    "projections": {2026: 88, 2027: 87, 2028: 85, 2029: 83, 2030: 80, 2031: 78, 2032: 75, 2033: 73, 2034: 71, 2035: 70}
                },
                "Hyderabad": {
                    "trend": "improving",
                    "driver": "Green city master plan, EV fleet expansion",
                    "projections": {2026: 100, 2027: 95, 2028: 90, 2029: 85, 2030: 80, 2031: 76, 2032: 72, 2033: 68, 2034: 65, 2035: 62}
                }
            },
            "USA": {
                "Los Angeles": {
                    "trend": "improving",
                    "driver": "California CARB regulations, zero-emission vehicle mandates",
                    "projections": {2026: 140, 2027: 132, 2028: 124, 2029: 116, 2030: 108, 2031: 100, 2032: 93, 2033: 87, 2034: 82, 2035: 76}
                },
                "New York": {
                    "trend": "improving",
                    "driver": "Climate Leadership and Community Protection Act, clean transit",
                    "projections": {2026: 65, 2027: 62, 2028: 59, 2029: 56, 2030: 52, 2031: 49, 2032: 46, 2033: 44, 2034: 42, 2035: 40}
                },
                "Chicago": {
                    "trend": "improving",
                    "driver": "Illinois Climate and Equitable Jobs Act, coal plant closures",
                    "projections": {2026: 76, 2027: 73, 2028: 70, 2029: 67, 2030: 63, 2031: 60, 2032: 57, 2033: 54, 2034: 52, 2035: 49}
                },
                "Houston": {
                    "trend": "improving",
                    "driver": "EPA refinery regulations, natural gas transition, clean port initiative",
                    "projections": {2026: 110, 2027: 105, 2028: 100, 2029: 95, 2030: 89, 2031: 84, 2032: 79, 2033: 75, 2034: 71, 2035: 67}
                },
                "Phoenix": {
                    "trend": "stable",
                    "driver": "Dust control programs offset by population growth; EVs improving ozone",
                    "projections": {2026: 124, 2027: 122, 2028: 119, 2029: 116, 2030: 112, 2031: 109, 2032: 105, 2033: 102, 2034: 99, 2035: 96}
                },
                "San Francisco": {
                    "trend": "improving",
                    "driver": "California clean energy grid, EV adoption, Bay Area AQMD rules",
                    "projections": {2026: 50, 2027: 48, 2028: 46, 2029: 44, 2030: 42, 2031: 40, 2032: 38, 2033: 37, 2034: 36, 2035: 35}
                },
                "Seattle": {
                    "trend": "stable",
                    "driver": "Clean Energy Transformation Act; wildfire smoke risk creates variability",
                    "projections": {2026: 45, 2027: 44, 2028: 43, 2029: 43, 2030: 42, 2031: 41, 2032: 40, 2033: 40, 2034: 39, 2035: 38}
                },
                "Denver": {
                    "trend": "improving",
                    "driver": "Colorado Air Pollution Control, ozone action plan, clean fleet rules",
                    "projections": {2026: 86, 2027: 83, 2028: 79, 2029: 75, 2030: 71, 2031: 68, 2032: 64, 2033: 61, 2034: 58, 2035: 55}
                },
                "Miami": {
                    "trend": "improving",
                    "driver": "Florida clean energy transition, coastal air quality monitoring",
                    "projections": {2026: 57, 2027: 55, 2028: 53, 2029: 51, 2030: 49, 2031: 47, 2032: 45, 2033: 44, 2034: 43, 2035: 42}
                },
                "Atlanta": {
                    "trend": "improving",
                    "driver": "Georgia clean air plans, EV corridor Southeast, transit expansion",
                    "projections": {2026: 93, 2027: 89, 2028: 85, 2029: 81, 2030: 77, 2031: 73, 2032: 70, 2033: 67, 2034: 64, 2035: 61}
                },
                "Boston": {
                    "trend": "improving",
                    "driver": "Massachusetts Clean Energy and Climate Plan, offshore wind expansion",
                    "projections": {2026: 61, 2027: 58, 2028: 56, 2029: 53, 2030: 50, 2031: 48, 2032: 46, 2033: 44, 2034: 42, 2035: 40}
                },
                "Portland": {
                    "trend": "stable",
                    "driver": "Oregon Clean Electricity Plan; wildfire smoke risk creates uncertainty",
                    "projections": {2026: 47, 2027: 46, 2028: 45, 2029: 45, 2030: 44, 2031: 43, 2032: 42, 2033: 42, 2034: 41, 2035: 40}
                },
                "Vancouver": {
                    "trend": "stable",
                    "driver": "Already clean; wildfire smoke risk may offset improvements",
                    "projections": {2026: 70, 2027: 68, 2028: 67, 2029: 65, 2030: 64, 2031: 63, 2032: 61, 2033: 60, 2034: 59, 2035: 58}
                },
                "Arlington": {
                    "trend": "improving",
                    "driver": "Federal sustainability programs, EV infrastructure expansion",
                    "projections": {2026: 72, 2027: 70, 2028: 67, 2029: 64, 2030: 61, 2031: 58, 2032: 56, 2033: 54, 2034: 52, 2035: 50}
                },
                "Dublin": {
                    "trend": "improving",
                    "driver": "California air district programs, clean energy transition",
                    "projections": {2026: 70, 2027: 67, 2028: 64, 2029: 61, 2030: 58, 2031: 55, 2032: 53, 2033: 51, 2034: 49, 2035: 47}
                }
            },
            "Canada": {
                "Vancouver": {
                    "trend": "stable",
                    "driver": "Clean air regulations; wildfire events create uncertainty",
                    "projections": {2026: 60, 2027: 59, 2028: 58, 2029: 57, 2030: 56, 2031: 55, 2032: 54, 2033: 53, 2034: 52, 2035: 51}
                }
            },
            "China": {
                "Beijing": {
                    "trend": "improving",
                    "driver": "Blue Sky Defense Plan, coal-to-gas/EV transition, heavy industry relocation",
                    "projections": {2026: 185, 2027: 168, 2028: 152, 2029: 138, 2030: 124, 2031: 112, 2032: 101, 2033: 92, 2034: 84, 2035: 76}
                },
                "Shanghai": {
                    "trend": "improving",
                    "driver": "Green finance initiatives, industrial emission caps",
                    "projections": {2026: 90, 2027: 85, 2028: 80, 2029: 74, 2030: 69, 2031: 64, 2032: 60, 2033: 56, 2034: 53, 2035: 50}
                }
            },
            "UK": {
                "London": {
                    "trend": "improving",
                    "driver": "ULEZ expansion, Net Zero 2050 target, clean energy grid",
                    "projections": {2026: 52, 2027: 50, 2028: 47, 2029: 45, 2030: 42, 2031: 40, 2032: 38, 2033: 36, 2034: 34, 2035: 32}
                }
            },
            "Ireland": {
                "Dublin": {
                    "trend": "improving",
                    "driver": "Climate Action Plan 2024, renewable energy targets, EV uptake",
                    "projections": {2026: 56, 2027: 54, 2028: 52, 2029: 50, 2030: 48, 2031: 46, 2032: 44, 2033: 43, 2034: 42, 2035: 40}
                }
            }
        }

        # Normalize and look up location
        location_clean = re.sub(r"[^A-Za-z\s,]", "", location or "").strip()
        parts = [p.strip().title() for p in location_clean.split(',') if p.strip()]
        city_query = parts[0] if parts else ""
        usa_context = self._is_usa_context(parts)

        # Try city lookup across all countries
        found_country = None
        found_city = None
        found_data = None

        for country, cities in longterm_data.items():
            if city_query in cities:
                found_country = country
                found_city = city_query
                found_data = cities[city_query]
                break
            if city_query == country:
                # Country-level summary
                report = f"\nLong-Term Air Quality Forecast: {country} (2026-2035)\n"
                report += "=" * 60 + "\n"
                for city, cdata in cities.items():
                    proj = cdata["projections"]
                    report += f"\n{city} (Trend: {cdata['trend'].title()}):\n"
                    report += f"  Driver: {cdata['driver']}\n"
                    report += "  Year  | AQI  | Level\n"
                    report += "  ------|------|-------------------------------\n"
                    for year in [2026, 2028, 2030, 2032, 2035]:
                        aqi = proj[year]
                        report += f"  {year}  | {aqi:<4} | {self._aqi_level(aqi)}\n"
                return report

        # Dynamic fallback for any US city not present in curated long-term list
        if not found_data:
            us_resolution_query = city_query if usa_context and city_query else f"{city_query}, USA"
            resolved = self._resolve_us_city(us_resolution_query)
            if resolved:
                resolved_city, lat, lon, admin = resolved
                live_data = self._fetch_live_air_quality(resolved_city, lat, lon)
                if live_data:
                    found_country = "USA"
                    found_city = f"{resolved_city}, {admin}"
                    found_data = self._build_us_longterm_projection(int(live_data.get("aqi", 80)))

        if not found_data:
            return self._get_available_cities_message(location)

        proj = found_data["projections"]
        trend = found_data["trend"]
        driver = found_data["driver"]

        # Calculate percentage improvement
        aqi_start = proj[2026]
        aqi_end = proj[2035]
        change_pct = round(abs(aqi_end - aqi_start) / aqi_start * 100, 1)
        direction = "improvement" if aqi_end < aqi_start else "increase"

        report = f"\nLong-Term Air Quality Forecast: {found_city}, {found_country}\n"
        report += "=" * 60 + "\n"
        report += f"Trend Outlook  : {trend.title()}\n"
        report += f"Key Driver     : {driver}\n"
        report += f"Overall Change : {change_pct}% {direction} by 2035\n\n"
        report += f"{'Year':<8} {'AQI':<8} {'Level':<35} {'Change'}\n"
        report += "-" * 70 + "\n"

        prev_aqi = None
        for year, aqi in sorted(proj.items()):
            delta = ""
            if prev_aqi is not None:
                diff = aqi - prev_aqi
                delta = f"{'[down]' if diff < 0 else '[up]'} {abs(diff)}"
            report += f"{year:<8} {aqi:<8} {self._aqi_level(aqi):<35} {delta}\n"
            prev_aqi = aqi

        report += "\n"
        report += "AQI Scale Reference:\n"
        report += "  0-50   Good | 51-100 Moderate | 101-150 Unhealthy for Sensitive Groups\n"
        report += "  151-200 Unhealthy | 201-300 Very Unhealthy | 301+ Hazardous\n"
        report += "\nNote: Projections are based on current policy trajectories and may vary\n"
        report += "with changes in regulation, climate events, or economic activity.\n"

        return report
    
    def get_environmental_health_index(self, region: str) -> str:
        """
        Get comprehensive environmental health index for a region
        
        Args:
            region: Geographic region
        
        Returns:
            Environmental health index report
        """
        
        report = f"""
Environmental Health Index for {region}
Report Date: {datetime.now().strftime('%Y-%m-%d')}

Composite Index Components:
1. Air Quality Index: 75/100 (Good)
2. Water Quality Index: 68/100 (Fair)
3. Biodiversity Index: 62/100 (Fair)
4. Green Cover Index: 80/100 (Good)
5. Waste Management Index: 70/100 (Good)

Overall Environmental Health Score: 71/100 (Fair to Good)

Key Findings:
- Air quality shows good improvement
- Water quality needs attention in some areas
- Green cover initiatives are succeeding
- Waste management improving steadily

Recommendations:
- Continue air quality monitoring
- Invest in water treatment facilities
- Expand biodiversity conservation
- Support green initiatives
"""
        
        return report
