# Main GreenMind Agent

import uuid
import time
import os
from typing import Dict, Any, List, Tuple
from datetime import datetime
import logging

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    from langchain.chat_models import ChatGoogleGenerativeAI
try:
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    from langchain.schema import HumanMessage, SystemMessage

from src.utils.config import GOOGLE_API_KEY, SYSTEM_PROMPT, VALID_TOPICS
from src.utils.logger import logger
from src.rag.vector_db import VectorDatabase
from src.tools.web_search_tool import WebSearchTool
from src.tools.pollution_index_tool import PollutionIndexTool
from src.tools.carbon_calculator import CarbonCalculatorTool

class GreenMindAgent:
    """
    Main GreenMind Agent - orchestrates RAG tools and external tools
    """
    
    def __init__(self, genai_api_key: str | None = None):
        """Initialize GreenMind Agent with all tools"""
        
        self.session_id = str(uuid.uuid4())
        self.genai_api_key = (genai_api_key or os.getenv("GOOGLE_API_KEY") or GOOGLE_API_KEY).strip()

        if not self.genai_api_key:
            raise ValueError(
                "GOOGLE_API_KEY is missing. Configure it in Streamlit Secrets or environment variables."
            )
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=self.genai_api_key,
            temperature=0.7,
            max_output_tokens=2048
        )
        
        # Initialize RAG tools
        self.vector_db = VectorDatabase()
        
        # Initialize external tools
        self.web_search_tool = WebSearchTool()
        self.pollution_tool = PollutionIndexTool()
        self.carbon_calculator = CarbonCalculatorTool()
        
        # Tool registry
        self.tools = {
            'rag_policies': self._rag_policies,
            'rag_effects': self._rag_effects,
            'web_search': self._web_search,
            'pollution_index': self._pollution_index,
            'carbon_calculator': self._carbon_calculator
        }
        
        logger.logger.info(f"GreenMind Agent initialized. Session: {self.session_id}")
    
    def chat(self, user_message: str) -> Dict[str, Any]:
        """
        Main chat interface
        
        Args:
            user_message: User's query
        
        Returns:
            Response dictionary with answer and metadata
        """
        
        start_time = time.time()
        
        try:
            # Log the query
            logger.log_query(user_message, self.session_id)
            
            # Check if query is environment-related
            is_environmental = self._is_environmental_query(user_message)
            
            if not is_environmental:
                response = {
                    "answer": "I appreciate your question! However, I'm specifically designed to help with environmental and sustainability topics. Could you ask me something about climate change, environmental policies, pollution, renewable energy, or other green initiatives? I'm here to help!",
                    "session_id": self.session_id,
                    "tools_used": [],
                    "processing_time_ms": int((time.time() - start_time) * 1000)
                }
                logger.log_response(response["answer"], self.session_id, response["processing_time_ms"])
                return response
            
            # Greeting with environmental quote
            if self._is_greeting(user_message):
                quote = self._get_environmental_quote()
                response_text = self._generate_greeting_response(quote)
            else:
                # Determine which tools to use
                tools_to_use = self._determine_tools(user_message)
                
                # Gather information from tools
                tool_results = self._execute_tools(tools_to_use, user_message)
                
                # Generate response using LLM
                response_text = self._generate_response(user_message, tool_results)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            response = {
                "answer": response_text,
                "session_id": self.session_id,
                "tools_used": list(tool_results.keys()) if not self._is_greeting(user_message) else [],
                "processing_time_ms": processing_time
            }
            
            logger.log_response(response_text, self.session_id, processing_time)
            
            return response
        
        except Exception as e:
            logger.log_error(str(e), "ChatException", self.session_id)
            return {
                "answer": f"I encountered an error processing your question: {str(e)}",
                "session_id": self.session_id,
                "error": str(e),
                "tools_used": []
            }
    
    def _is_environmental_query(self, query: str) -> bool:
        """Check if query is about environmental topics"""
        
        environmental_keywords = [
            "environment", "climate", "carbon", "pollution", "renewable",
            "sustainability", "green", "energy", "ecology", "ecosystem",
            "conservation", "emission", "recycling", "waste", "air quality",
            "water quality", "biodiversity", "deforestation", "warming",
            "sustainable", "eco", "nature", "planet", "fossil fuel",
            "carbon footprint", "climate change", "global warming"
        ]
        
        query_lower = query.lower()
        
        # Check if any environmental keyword is in the query
        for keyword in environmental_keywords:
            if keyword in query_lower:
                return True
        
        return False
    
    def _is_greeting(self, query: str) -> bool:
        """Check if query is a greeting"""
        
        greetings = ["hello", "hi", "hey", "greetings", "good morning", 
                    "good afternoon", "good evening", "how are you"]
        
        query_lower = query.lower().strip()
        
        for greeting in greetings:
            if greeting in query_lower:
                return True
        
        return False
    
    def _get_environmental_quote(self) -> str:
        """Get a random environmental quote"""
        
        quotes = [
            "In every walk with nature, one receives far more than he seeks. - John Muir",
            "The environment is where we all meet; where all have a mutual interest. - Lady Bird Johnson",
            "The greatest threat to our planet is the belief that someone else will save it. - Robert Swan",
            "We do not inherit the earth from our ancestors; we borrow it from our children. - Native American Proverb",
            "The Earth does not belong to us; we belong to the Earth. - Chief Seattle",
            "The future will either be green or not at all. - Bob Brown",
            "What we do to the Earth, we do to ourselves. - Chief Seattle"
        ]
        
        import random
        return random.choice(quotes)
    
    def _generate_greeting_response(self, quote: str) -> str:
        """Generate greeting response with environmental quote"""
        
        greeting = f"""Hello! Welcome to GreenMind, your intelligent sustainability advisor. 🌍

I'm here to help you with questions about environmental policies, climate change, sustainability, 
pollution, renewable energy, and all things related to protecting our planet and creating a greener future.

Here's a thought for you:
"{quote}"

How can I assist you today? Feel free to ask about:
• Environmental policies and regulations
• Climate change and global warming effects
• Sustainability practices and green initiatives
• Air and water quality data
• Carbon footprint calculations and reduction strategies
• Renewable energy solutions"""
        
        return greeting
    
    def _determine_tools(self, query: str) -> List[str]:
        """Determine which tools are relevant for the query"""
        
        tools_to_use = []
        query_lower = query.lower()
        
        # Check for policy-related queries
        if any(word in query_lower for word in ["policy", "law", "regulation", "government", "mandate", "act"]):
            tools_to_use.append('rag_policies')
        
        # Check for effects/impacts queries
        if any(word in query_lower for word in ["effect", "impact", "cause", "degradation", "damage", "harm"]):
            tools_to_use.append('rag_effects')
        
        # Check for news/current affairs
        if any(word in query_lower for word in ["news", "current", "recent", "today", "happening", "latest"]):
            tools_to_use.append('web_search')
        
        # Check for pollution/air quality
        if any(word in query_lower for word in ["pollution", "air quality", "aqi", "pm2.5", "health", "forecast"]):
            tools_to_use.append('pollution_index')
        
        # Check for carbon/footprint
        if any(word in query_lower for word in ["carbon", "footprint", "emissions", "co2", "transport", "energy"]):
            tools_to_use.append('carbon_calculator')
        
        # Default to both RAG tools if no specific tool identified
        if not tools_to_use:
            tools_to_use = ['rag_policies', 'rag_effects', 'web_search']
        
        return tools_to_use
    
    def _execute_tools(self, tools: List[str], query: str) -> Dict[str, str]:
        """Execute specified tools"""
        
        results = {}
        
        for tool in tools:
            if tool in self.tools:
                try:
                    result = self.tools[tool](query)
                    results[tool] = result
                    logger.log_tool_usage(tool, query, result, self.session_id)
                except Exception as e:
                    logger.log_error(f"Tool {tool} failed: {str(e)}", "ToolException", self.session_id)
                    results[tool] = f"Error using {tool}: {str(e)}"
        
        return results
    
    def _rag_policies(self, query: str) -> str:
        """RAG retrieval for environmental policies"""
        
        try:
            results = self.vector_db.retrieve(query, k=3, source='policies')
            
            if not results:
                return "No relevant environmental policies found in database."
            
            documents = [result[0].page_content for result in results]
            logger.log_rag_retrieval(query, documents, 'policies', self.session_id)
            
            return "\n---\n".join(documents[:3])
        except Exception as e:
            return f"Error retrieving policies: {str(e)}"
    
    def _rag_effects(self, query: str) -> str:
        """RAG retrieval for environmental effects"""
        
        try:
            results = self.vector_db.retrieve(query, k=3, source='effects')
            
            if not results:
                return "No relevant environmental effects information found in database."
            
            documents = [result[0].page_content for result in results]
            logger.log_rag_retrieval(query, documents, 'effects', self.session_id)
            
            return "\n---\n".join(documents[:3])
        except Exception as e:
            return f"Error retrieving environmental effects: {str(e)}"
    
    def _web_search(self, query: str) -> str:
        """Web search tool"""
        
        try:
            results = self.web_search_tool.search(query, num_results=3)
            return results
        except Exception as e:
            return f"Error performing web search: {str(e)}"
    
    def _pollution_index(self, query: str) -> str:
        """Get pollution index and air quality data"""
        
        try:
            # Extract location from query
            location = self._extract_location(query)
            
            if location:
                return self.pollution_tool.get_air_quality(location)
            else:
                return "Please specify a location (city/country) to get air quality data."
        except Exception as e:
            return f"Error retrieving pollution data: {str(e)}"
    
    def _carbon_calculator(self, query: str) -> str:
        """Calculate carbon footprint"""
        
        try:
            # This is a simplified version - in a full implementation,
            # we would parse the query for specific values
            advice = "Carbon Calculator Tool:\n\n"
            advice += "I can help you calculate your carbon footprint from:\n"
            advice += "• Transportation (car, bus, train, flight)\n"
            advice += "• Energy consumption (electricity, gas)\n"
            advice += "• Food consumption (meat, vegetables, dairy)\n\n"
            advice += "Please specify your activities with details like:\n"
            advice += "- 'I drive 50 km per day'\n"
            advice += "- 'My monthly electricity bill is 500 kWh'\n"
            advice += "- 'I eat meat 5 times a week'\n"
            
            return advice
        except Exception as e:
            return f"Error calculating carbon footprint: {str(e)}"
    
    def _extract_location(self, query: str) -> str:
        """Extract location from query"""
        
        locations = ["delhi", "mumbai", "bangalore", "london", "newyork", 
                    "beijing", "shanghai", "india", "usa", "uk", "china"]
        
        query_lower = query.lower()
        
        for location in locations:
            if location in query_lower:
                return location.title()
        
        return None
    
    def _generate_response(self, query: str, tool_results: Dict[str, str]) -> str:
        """Generate final response using LLM"""
        
        try:
            # Prepare context from tool results
            context = "Tool Results:\n"
            for tool_name, result in tool_results.items():
                context += f"\n{tool_name}:\n{result}\n"
            
            # Create messages for LLM
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"User query: {query}\n\n{context}\n\nPlease provide a comprehensive and helpful response based on the above information.")
            ]
            
            # Get response from LLM
            response = self.llm(messages)
            
            return response.content
        
        except Exception as e:
            logger.log_error(str(e), "LLMException", self.session_id)
            # Fallback response
            return f"I apologize, but I had trouble generating a detailed response. However, based on the information gathered, I can tell you that your question about environmental topics is important. Please try rephrasing your question for a more specific answer."
    
    def get_session_summary(self) -> Dict:
        """Get summary of current session"""
        
        return logger.get_session_summary(self.session_id)
    
    def save_logs(self):
        """Save session logs"""
        
        logger.save_structured_logs()
