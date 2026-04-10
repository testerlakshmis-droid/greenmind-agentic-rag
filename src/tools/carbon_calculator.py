# Carbon Footprint Calculator Tool

import logging
from typing import Dict

logger = logging.getLogger("GreenMind")

class CarbonCalculatorTool:
    """
    Tool for calculating carbon footprint based on various activities
    """
    
    def __init__(self):
        self.name = "carbon_calculator"
        self.description = "Calculate carbon footprint from transportation, energy, and food consumption"
        
        # Carbon emission factors (kg CO2 per unit)
        self.emission_factors = {
            "transport": {
                "car": 0.21,  # kg CO2 per km
                "bus": 0.089,  # kg CO2 per km
                "train": 0.041,  # kg CO2 per km
                "flight": 0.255,  # kg CO2 per km
                "motorcycle": 0.15  # kg CO2 per km
            },
            "energy": {
                "electricity": 0.85,  # kg CO2 per kWh (varies by region)
                "natural_gas": 2.04,  # kg CO2 per cubic meter
                "coal": 2.37  # kg CO2 per kWh
            },
            "food": {
                "beef": 27,  # kg CO2 per kg of food
                "pork": 12,  # kg CO2 per kg of food
                "chicken": 6.9,  # kg CO2 per kg of food
                "fish": 5.9,  # kg CO2 per kg of food
                "vegetables": 2,  # kg CO2 per kg of food
                "dairy": 3  # kg CO2 per kg of food
            }
        }
    
    def calculate_transport_emissions(self, mode: str, distance_km: float) -> Dict:
        """
        Calculate emissions from transportation
        
        Args:
            mode: Type of transport (car, bus, train, flight)
            distance_km: Distance traveled in kilometers
        
        Returns:
            Calculation result dictionary
        """
        
        # Validate inputs
        if not mode or not isinstance(mode, str):
            return {"error": "Transport mode must be a non-empty string"}
        
        try:
            distance_km = float(distance_km)
        except (ValueError, TypeError):
            return {"error": "Distance must be a valid number"}
        
        # Validate distance bounds
        if distance_km < 0:
            return {"error": "Distance cannot be negative"}
        if distance_km > 1_000_000:
            return {"error": "Distance exceeds reasonable limit (1,000,000 km)"}
        
        mode_lower = mode.lower().strip()
        
        if mode_lower not in self.emission_factors["transport"]:
            return {
                "error": f"Unknown transport mode. Available: {', '.join(self.emission_factors['transport'].keys())}"
            }
        
        emission_factor = self.emission_factors["transport"][mode_lower]
        emissions = emission_factor * distance_km
        
        return {
            "mode": mode,
            "distance_km": distance_km,
            "emission_factor": emission_factor,
            "total_emissions_kg": round(emissions, 2),
            "total_emissions_tons": round(emissions / 1000, 3),
            "equivalent_trees_needed": round(emissions / 21, 1)  # 1 tree absorbs ~21kg CO2/year
        }
    
    def calculate_energy_emissions(self, energy_type: str, consumption: float) -> Dict:
        """
        Calculate emissions from energy consumption
        
        Args:
            energy_type: Type of energy (electricity, natural_gas, coal)
            consumption: Amount consumed (kWh or m³)
        
        Returns:
            Calculation result dictionary
        """
        
        # Validate inputs
        if not energy_type or not isinstance(energy_type, str):
            return {"error": "Energy type must be a non-empty string"}
        
        try:
            consumption = float(consumption)
        except (ValueError, TypeError):
            return {"error": "Consumption must be a valid number"}
        
        # Validate consumption bounds
        if consumption < 0:
            return {"error": "Consumption cannot be negative"}
        if consumption > 10_000_000:
            return {"error": "Consumption exceeds reasonable limit (10,000,000 units)"}
        
        energy_lower = energy_type.lower().strip()
        
        if energy_lower not in self.emission_factors["energy"]:
            return {
                "error": f"Unknown energy type. Available: {', '.join(self.emission_factors['energy'].keys())}"
            }
        
        emission_factor = self.emission_factors["energy"][energy_lower]
        emissions = emission_factor * consumption
        
        unit = "kWh" if energy_lower != "natural_gas" else "m³"
        
        return {
            "energy_type": energy_type,
            "consumption": consumption,
            "unit": unit,
            "emission_factor": emission_factor,
            "total_emissions_kg": round(emissions, 2),
            "total_emissions_tons": round(emissions / 1000, 3)
        }
    
    def calculate_food_emissions(self, food_type: str, quantity_kg: float) -> Dict:
        """
        Calculate emissions from food production and consumption
        
        Args:
            food_type: Type of food (beef, chicken, vegetables, etc.)
            quantity_kg: Quantity consumed in kilograms
        
        Returns:
            Calculation result dictionary
        """
        
        # Validate inputs
        if not food_type or not isinstance(food_type, str):
            return {"error": "Food type must be a non-empty string"}
        
        try:
            quantity_kg = float(quantity_kg)
        except (ValueError, TypeError):
            return {"error": "Quantity must be a valid number"}
        
        # Validate quantity bounds
        if quantity_kg < 0:
            return {"error": "Quantity cannot be negative"}
        if quantity_kg > 100_000:
            return {"error": "Quantity exceeds reasonable limit (100,000 kg)"}
        
        food_lower = food_type.lower().strip()
        
        if food_lower not in self.emission_factors["food"]:
            return {
                "error": f"Unknown food type. Available: {', '.join(self.emission_factors['food'].keys())}"
            }
        
        emission_factor = self.emission_factors["food"][food_lower]
        emissions = emission_factor * quantity_kg
        
        return {
            "food_type": food_type,
            "quantity_kg": quantity_kg,
            "emission_factor": emission_factor,
            "total_emissions_kg": round(emissions, 2),
            "total_emissions_tons": round(emissions / 1000, 3)
        }
    
    def calculate_daily_footprint(self, params: Dict) -> Dict:
        """
        Calculate daily carbon footprint from various activities
        
        Args:
            params: Dictionary with keys like:
                - car_km: kilometers traveled by car
                - public_transport_km: kilometers on public transport
                - electricity_kwh: electricity consumption
                - meat_kg: meat consumption
        
        Returns:
            Daily footprint summary
        """
        
        if not isinstance(params, dict):
            return {"error": "Parameters must be provided as a dictionary"}
        
        total_emissions = 0
        breakdown = {}
        
        def _safe_float(val, default=0.0):
            """Safely convert param values to non-negative floats."""
            try:
                result = float(val)
                return max(0.0, result)
            except (ValueError, TypeError):
                return default
        
        # Transport
        car_km = _safe_float(params.get("car_km", 0))
        if car_km > 0:
            result = self.calculate_transport_emissions("car", car_km)
            if "error" not in result:
                breakdown["car"] = result["total_emissions_kg"]
                total_emissions += result["total_emissions_kg"]
        
        pub_km = _safe_float(params.get("public_transport_km", 0))
        if pub_km > 0:
            result = self.calculate_transport_emissions("bus", pub_km)
            if "error" not in result:
                breakdown["public_transport"] = result["total_emissions_kg"]
                total_emissions += result["total_emissions_kg"]
        
        # Energy
        elec_kwh = _safe_float(params.get("electricity_kwh", 0))
        if elec_kwh > 0:
            result = self.calculate_energy_emissions("electricity", elec_kwh)
            if "error" not in result:
                breakdown["electricity"] = result["total_emissions_kg"]
                total_emissions += result["total_emissions_kg"]
        
        # Food
        meat_kg = _safe_float(params.get("meat_kg", 0))
        if meat_kg > 0:
            result = self.calculate_food_emissions("beef", meat_kg)
            if "error" not in result:
                breakdown["meat"] = result["total_emissions_kg"]
                total_emissions += result["total_emissions_kg"]
        
        return {
            "daily_emissions_kg": round(total_emissions, 2),
            "daily_emissions_tons": round(total_emissions / 1000, 3),
            "annual_emissions_tons": round((total_emissions * 365) / 1000, 2),
            "breakdown": breakdown
        }
    
    def get_reduction_advice(self, emissions_kg: float) -> str:
        """
        Get personalized advice for reducing carbon footprint
        
        Args:
            emissions_kg: Current emissions in kg CO2
        
        Returns:
            Personalized reduction advice
        """
        
        try:
            emissions_kg = float(emissions_kg)
        except (ValueError, TypeError):
            return "Error: emissions_kg must be a valid number."
        
        if emissions_kg < 0:
            return "Error: emissions_kg cannot be negative."
        
        advice = "Carbon Footprint Reduction Advice:\n\n"
        
        if emissions_kg > 50:
            advice += "🔴 HIGH EMISSIONS - Consider significant lifestyle changes:\n"
            advice += "  • Switch to electric or hybrid vehicle\n"
            advice += "  • Use public transportation more often\n"
            advice += "  • Reduce meat consumption (especially beef)\n"
            advice += "  • Improve home energy efficiency\n"
        elif emissions_kg > 25:
            advice += "🟡 MODERATE EMISSIONS - Good opportunities for improvement:\n"
            advice += "  • Combine trips to reduce driving\n"
            advice += "  • Try meatless days\n"
            advice += "  • Use renewable energy if available\n"
            advice += "  • Improve insulation and heating efficiency\n"
        else:
            advice += "🟢 LOW EMISSIONS - Great job! Keep it up:\n"
            advice += "  • Continue sustainable practices\n"
            advice += "  • Explore carbon offset options\n"
            advice += "  • Help others reduce their footprint\n"
        
        # Calculate offset information
        trees_needed = round(emissions_kg / 21, 1)
        advice += f"\nTo offset today's emissions, approximately {trees_needed} trees would be needed to absorb the CO2 over one year."
        
        return advice
