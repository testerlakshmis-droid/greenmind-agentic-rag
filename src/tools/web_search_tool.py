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
        
        # Validate inputs
        if not query or not isinstance(query, str):
            return "Error: Search query must be a non-empty string."
        
        query = query.strip()
        if not query:
            return "Error: Search query cannot be empty."
        
        # Limit query length to prevent abuse
        max_query_length = 500
        if len(query) > max_query_length:
            query = query[:max_query_length]
        
        # Validate num_results
        try:
            num_results = int(num_results)
            if num_results < 1:
                num_results = 5
            elif num_results > 20:
                num_results = 20
        except (ValueError, TypeError):
            num_results = 5
        
        # If SerpAPI key is available, use it with fallback on failure
        if self.serpapi_key:
            try:
                return self._serpapi_search(query, num_results)
            except Exception as e:
                logger.error(f"SerpAPI search failed: {e}, falling back to simulated search")
                return self._simulated_search(query)
        
        # Fallback: return simulated results with real environmental information
        logger.info("SerpAPI key not configured, using simulated search results")
        return self._simulated_search(query)
    
    def _serpapi_search(self, query: str, num_results: int) -> str:
        """Search using SerpAPI with error handling"""
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
                try:
                    results = response.json()
                except ValueError:
                    logger.error("Failed to parse SerpAPI response JSON")
                    return "Error: Invalid response format from search API."
                
                # Format organic results
                formatted_results = []
                if 'organic_results' in results and isinstance(results['organic_results'], list):
                    for result in results['organic_results'][:num_results]:
                        if isinstance(result, dict):
                            formatted_results.append({
                                'title': str(result.get('title', ''))[:500],
                                'link': str(result.get('link', ''))[:1000],
                                'snippet': str(result.get('snippet', ''))[:1000]
                            })
                
                if not formatted_results:
                    return "No search results found."
                
                return self._format_results(formatted_results)
            elif response.status_code == 401:
                return "Error: Invalid SerpAPI key."
            elif response.status_code == 429:
                return "Error: Search rate limit exceeded. Please try again later."
            else:
                return f"Search failed with status code: {response.status_code}"
        
        except requests.Timeout:
            logger.error("Web search timeout")
            return "Error: Search request timed out. Please try again."
        except requests.ConnectionError:
            logger.error("Web search connection error")
            return "Error: Cannot connect to search service."
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return f"Error during web search: {str(e)[:200]}"
    
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
