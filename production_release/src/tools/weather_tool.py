from datetime import datetime
from difflib import get_close_matches
try:
    from utils.location_disambiguation import format_ambiguity_prompt, get_city_ambiguity_description
except ImportError:
    from src.utils.location_disambiguation import format_ambiguity_prompt, get_city_ambiguity_description

class WeatherTool:
    """A lightweight simulated weather tool for environmental context."""

    def __init__(self):
        self.name = "weather_tool"
        self.description = "Provides current weather conditions for known cities."
        self.weather_data = {
            "India": {
                "Delhi": {"temp": 34, "condition": "Sunny", "humidity": 45, "wind": 10},
                "Mumbai": {"temp": 29, "condition": "Humid", "humidity": 72, "wind": 12},
                "Bangalore": {"temp": 26, "condition": "Clear", "humidity": 55, "wind": 8},
                "Hyderabad": {"temp": 33, "condition": "Hot", "humidity": 38, "wind": 9}
            },
            "USA": {
                "Los Angeles": {"temp": 24, "condition": "Cloudy", "humidity": 60, "wind": 14},
                "New York": {"temp": 12, "condition": "Rainy", "humidity": 82, "wind": 16},
                "Dublin": {"temp": 10, "condition": "Overcast", "humidity": 78, "wind": 11},
                "Vancouver": {"temp": 13, "condition": "Cloudy", "humidity": 80, "wind": 12},
                "Arlington": {"temp": 23, "condition": "Partly Cloudy", "humidity": 58, "wind": 13}
            },
            "Canada": {
                "Vancouver": {"temp": 11, "condition": "Drizzle", "humidity": 84, "wind": 10}
            },
            "Ireland": {
                "Dublin": {"temp": 12, "condition": "Drizzle", "humidity": 76, "wind": 14}
            },
            "China": {
                "Beijing": {"temp": 17, "condition": "Windy", "humidity": 48, "wind": 20}
            },
            "UK": {
                "London": {"temp": 11, "condition": "Drizzle", "humidity": 73, "wind": 9}
            }
        }

    def get_weather(self, location: str) -> str:
        location_clean = (location or "").strip()
        if not location_clean:
            return "Please specify a city for weather data."

        parts = [p.strip().title() for p in location_clean.split(',') if p.strip()]
        city_query = parts[0]

        # Allow input styles such as "Dublin, CA, USA" or "Dublin, Ireland"
        country_query = None
        if len(parts) == 2:
            country_query = parts[1]
        elif len(parts) >= 3:
            country_query = parts[-1]
            state_query = parts[1]
            if country_query in ["Us", "Usa", "United States", "United States Of America", "U.s.a."]:
                country_query = "USA"
            if state_query == "Ca":
                country_query = "USA"

        if country_query:
            if country_query in ["Us", "Usa", "United States", "United States Of America", "U.s.a."]:
                country_query = "USA"

            country_data = self.weather_data.get(country_query)
            if country_data and city_query in country_data:
                return self._format_report(city_query, country_query, country_data[city_query])

            if country_query == "USA" and city_query in self.weather_data.get("USA", {}):
                return self._format_report(city_query, "USA", self.weather_data["USA"][city_query])

            return (
                f"No weather data found for '{city_query}, {country_query}'. "
                "Please check the spelling and include state/country, e.g., 'Dublin, Ireland' or 'Dublin, USA'."
            )

        city_query_lower = city_query.lower()

        matches = []
        for country, cities in self.weather_data.items():
            if city_query in cities:
                matches.append((country, cities[city_query]))

        if len(matches) == 1:
            country, weather_info = matches[0]
            return self._format_report(city_query, country, weather_info)

        if len(matches) > 1:
            regions = {country for country, _ in matches}
            return format_ambiguity_prompt(city_query, regions)

        desc = get_city_ambiguity_description(city_query)
        if desc:
            return (
                f"The city '{city_query}' may refer to multiple areas ({desc}). "
                "Please specify city, state, and country (example: 'Kansas City, Missouri, USA')."
            )

        known_cities = [city for country in self.weather_data.values() for city in country.keys()]
        close_matches = get_close_matches(city_query, known_cities, n=3, cutoff=0.6)
        if close_matches:
            suggestions = ', '.join(close_matches)
            return (
                f"I don't have exact weather data for '{city_query}', but did you mean: {suggestions}? "
                "Please include state and country if known."
            )

        return self._get_available_cities_message(city_query)

    def _get_available_cities_message(self, query: str) -> str:
        """Generate a message showing all available countries and cities"""
        message = f"Sorry, I'm not trained on '{query}'.\n\n"
        message += "Here are the countries and cities I have weather data for:\n\n"
        
        for country, cities in self.weather_data.items():
            city_list = ', '.join(sorted(cities.keys()))
            message += f"• {country}: {city_list}\n"
        
        message += "\nPlease select a city from the list above and specify it as 'City, Country' (e.g., 'Dublin, Ireland')."
        return message

    def _format_report(self, city, country, data):
        return (
            f"Weather Report for {city}, {country} (as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):\n"
            f"Temperature: {data['temp']}C\n"
            f"Condition: {data['condition']}\n"
            f"Humidity: {data['humidity']}%\n"
            f"Wind Speed: {data['wind']} km/h\n"
            "\nNote: For accurate local weather, please consult a live weather service."
        )
