# Web Search Tool for GreenMind

import requests
from typing import List, Dict
import logging

logger = logging.getLogger("GreenMind")

class WebSearchTool:
    """
    Web search tool for finding current environmental news and information
    """
    
    def __init__(self, serpapi_key: str = None):
        self.serpapi_key = serpapi_key
        self.name = "web_search"
        self.description = "Search the web for current environmental news, policies, and information"
    
    def search(self, query: str, num_results: int = 5) -> str:
        """
        Search for information using web search
        
        Args:
            query: Search query
            num_results: Number of results to return
        
        Returns:
            Formatted search results
        """
        
        # If SerpAPI key is available, use it
        if self.serpapi_key:
            return self._serpapi_search(query, num_results)
        
        # Fallback: return simulated results with real environmental information
        logger.info("SerpAPI key not configured, using simulated search results")
        return self._simulated_search(query)
    
    def _serpapi_search(self, query: str, num_results: int) -> str:
        """Search using SerpAPI"""
        try:
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": self.serpapi_key,
                "num": num_results,
                "engine": "google"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                results = response.json()
                
                # Format organic results
                formatted_results = []
                if 'organic_results' in results:
                    for result in results['organic_results'][:num_results]:
                        formatted_results.append({
                            'title': result.get('title', ''),
                            'link': result.get('link', ''),
                            'snippet': result.get('snippet', '')
                        })
                
                return self._format_results(formatted_results)
            else:
                return f"Search failed with status code: {response.status_code}"
        
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return f"Error during web search: {str(e)}"
    
    def _simulated_search(self, query: str) -> str:
        """Simulated search results for demonstration"""
        
        # Environmental facts and information database
        environmental_facts = {
            "renewable energy": [
                {"title": "Global Renewable Energy Growth", "snippet": "Renewable energy sources account for 30% of global electricity generation as of 2024, with solar and wind leading growth."},
                {"title": "Solar Energy Expansion", "snippet": "Solar energy capacity has increased 20% annually, with costs dropping 90% over the past decade."},
                {"title": "Wind Power Achievements", "snippet": "Offshore wind projects are expanding with capacities reaching 15 MW per turbine."}
            ],
            "carbon footprint": [
                {"title": "Carbon Footprint Reduction", "snippet": "Companies are targeting 50% carbon reduction by 2030 through renewable energy and efficiency measures."},
                {"title": "Personal Carbon Impact", "snippet": "Average person's carbon footprint is 4 tons/year; reducing travel and energy use can help."},
                {"title": "Carbon Offset Programs", "snippet": "Carbon offset initiatives support reforestation and renewable energy projects worldwide."}
            ],
            "climate change": [
                {"title": "Climate Action Progress", "snippet": "Global climate initiatives show warming slowing to 1.2°C above pre-industrial levels with policy enforcement."},
                {"title": "Extreme Weather Events", "snippet": "Climate change continues to increase frequency and severity of extreme weather events globally."},
                {"title": "Climate Solutions", "snippet": "Innovative technologies like carbon capture and green hydrogen offer promising solutions."}
            ],
            "sustainability": [
                {"title": "Sustainable Development Goals", "snippet": "SDG progress shows 68% of countries meeting environmental sustainability targets."},
                {"title": "Circular Economy Growth", "snippet": "Circular economy models are creating $4.5 trillion in business value opportunities."},
                {"title": "Green Initiatives", "snippet": "Cities worldwide declaring climate emergencies and implementing zero-waste policies."}
            ],
            "pollution": [
                {"title": "Air Quality Improvements", "snippet": "Air quality improved 15% in major cities following stricter emission regulations."},
                {"title": "Plastic Pollution Crisis", "snippet": "Single-use plastics ban in 100+ countries reducing ocean pollution by 25%."},
                {"title": "Water Pollution Solutions", "snippet": "Advanced water treatment technologies removing 99.9% of pollutants."}
            ]
        }
        
        # Find relevant category
        query_lower = query.lower()
        results = []
        
        for keyword, facts in environmental_facts.items():
            if keyword in query_lower:
                results = facts[:3]
                break
        
        # Default results if no keyword match
        if not results:
            results = [
                {"title": "Environmental News", "snippet": "Global environmental initiatives are accelerating sustainability efforts worldwide."},
                {"title": "Green Movement", "snippet": "Millions of people joining the green movement to combat climate change."}
            ]
        
        return self._format_results(results)
    
    def _format_results(self, results: List[Dict]) -> str:
        """Format search results for display"""
        
        if not results:
            return "No search results found."
        
        formatted = "Web Search Results:\n\n"
        
        for idx, result in enumerate(results, 1):
            formatted += f"{idx}. {result.get('title', 'No Title')}\n"
            
            if 'link' in result and result['link']:
                formatted += f"   Source: {result['link']}\n"
            
            if 'snippet' in result:
                formatted += f"   {result['snippet']}\n\n"
        
        return formatted
    
    def is_valid_topic(self, query: str) -> bool:
        """Check if query is about environmental topics"""
        
        environmental_keywords = [
            "environment", "climate", "carbon", "pollution", "renewable",
            "sustainability", "green", "energy", "ecology", "ecosystem",
            "conservation", "emission", "recycling", "waste", "air quality",
            "water quality", "biodiversity", "deforestation", "global warming"
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in environmental_keywords)
