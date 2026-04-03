#!/usr/bin/env python3
"""
GreenMind Agentic RAG - Gradio Web Interface
Works with Python 3.14 (alternative to Streamlit)
"""

import sys
import os
import re
import socket
import warnings
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Suppress known third-party warning noise on Python 3.14 while keeping runtime behavior unchanged.
warnings.filterwarnings(
    "ignore",
    message="Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message="You are sending unauthenticated requests to the HF Hub.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message="The class `HuggingFaceEmbeddings` was deprecated in LangChain.*",
    category=Warning,
)

# Reduce non-actionable startup logs from dependency internals.
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

import gradio as gr
import json
from datetime import datetime

# Load environment
from dotenv import load_dotenv
load_dotenv()

from utils.config import SYSTEM_PROMPT, GOOGLE_API_KEY
from utils.location_disambiguation import (
    build_city_country_map,
    detect_ambiguous_city,
    format_ambiguity_prompt,
)
from rag.vector_db import VectorDatabase
from tools.web_search_tool import WebSearchTool
from tools.pollution_index_tool import PollutionIndexTool
from tools.carbon_calculator import CarbonCalculatorTool
from tools.weather_tool import WeatherTool

# Initialize components
print("Initializing GreenMind components...")
vector_db = VectorDatabase()
web_search = WebSearchTool()
pollution_tool = PollutionIndexTool()
carbon_calc = CarbonCalculatorTool()
weather_tool = WeatherTool()
print("[OK] All components loaded!")

# Store conversation history
conversation_history = []

# Environmental health greeting quotes
environmental_quotes = [
    "[EARTH] 'The greatest threat to our planet is the belief that someone else will save it.' - Robert Swan",
    "[RECYCLE] 'Climate change is not just an environmental issue - it''s a health crisis that demands urgent action.' - WHO",
    "[LEAF] 'Healthy ecosystems lead to healthy communities. Protecting nature protects human health.' - UN",
    "[HEART] 'Every action to reduce carbon emissions is an investment in public health.' - Environmental Health Alliance",
    "[NATURAL] 'Clean air, clean water, and healthy soil are the foundations of human survival and wellbeing.' - CDC",
    "[WATER] 'Pollution doesn''t just harm the environment - it claims millions of lives yearly through disease.' - The Lancet",
    "[SUN] 'Renewable energy is the path to both environmental sustainability and improved public health outcomes.' - IRENA",
    "[BUTTERFLY] 'Biodiversity loss threatens food security and increases infectious disease outbreaks in human populations.' - IPBES"
]

import random

def get_greeting() -> str:
    """Generate greeting with environmental health quote"""
    quote = random.choice(environmental_quotes)
    greeting = f"""
## Welcome to GreenMind - Your Environmental Health Advisor

{quote}

### About GreenMind
Your intelligent sustainability advisor powered by:
- **RAG**: 134 environmental documents
- **AI**: Multi-tool agent orchestration  
- **Tools**: Web search, pollution index, carbon calculator

**System Status:** [OK] All components active
"""
    return greeting

def rag_search(query: str) -> str:
    """Search RAG database for relevant documents"""
    try:
        def format_doc_result(doc, score: float) -> str:
            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            metadata = getattr(doc, "metadata", {}) or {}
            file_name = metadata.get("file_name", "")
            title = Path(file_name).stem.replace('_', ' ') if file_name else "Document"

            # Normalize whitespace/newlines for cleaner one-line snippet in chat.
            snippet = re.sub(r"\s+", " ", content or "").strip()
            snippet = snippet[:220] + ("..." if len(snippet) > 220 else "")
            return f"- {title}: {snippet}"

        query_lower = (query or "").lower()
        policy_terms = [
            "policy", "regulation", "act", "law", "framework", "superfund", "rcra", "tsca", "nepa",
            "clean water", "clean air", "endangered species", "waste management", "cercla", "inflation reduction"
        ]
        effect_terms = [
            "effect", "effects", "impact", "impacts", "cause", "causes", "degradation", "health effect", "consequence", "consequences"
        ]

        is_policy_query = any(
            re.search(rf"\b{re.escape(term)}\b", query_lower) is not None
            for term in policy_terms
        )
        is_effect_query = any(
            re.search(rf"\b{re.escape(term)}\b", query_lower) is not None
            for term in effect_terms
        )

        policies = []
        effects = []
        if is_policy_query and not is_effect_query:
            policies = vector_db.retrieve(query, k=3, source='policies')
        elif is_effect_query and not is_policy_query:
            effects = vector_db.retrieve(query, k=3, source='effects')
        else:
            # Mixed/unknown intent: search both sources.
            policies = vector_db.retrieve(query, k=3, source='policies')
            effects = vector_db.retrieve(query, k=3, source='effects')
        
        results = []
        if policies:
            results.append("\nENVIRONMENTAL POLICIES:")
            # For policy intent, emphasize the strongest match first.
            limit = 1 if is_policy_query and not is_effect_query else 2
            for doc, score in policies[:limit]:
                results.append(format_doc_result(doc, score))
        
        if effects:
            results.append("\nENVIRONMENTAL EFFECTS:")
            for doc, score in effects[:2]:
                results.append(format_doc_result(doc, score))
        
        if results:
            return "\n".join(results)
        else:
            # If no results found, show available documents
            return get_available_documents_message(query)
    except Exception as e:
        return f"Error searching RAG: {e}"

def get_available_documents_message(query: str) -> str:
    """Show available environmental documents when no search results found"""
    from pathlib import Path
    
    message = f"Sorry, I'm not trained on '{query}'.\n\n"
    message += "Here are the environmental documents and topics I can discuss:\n\n"
    
    data_dir = Path(__file__).parent / "data"
    
    # List policies
    policies_dir = data_dir / "environmental_policies"
    if policies_dir.exists():
        pdf_policies = sorted(policies_dir.glob("*.pdf"))
        if pdf_policies:
            policies = sorted([f.stem.replace('_', ' ') for f in pdf_policies])
        else:
            policies = sorted([f.stem.replace('_', ' ') for f in policies_dir.glob("*.txt")])
        message += f"ENVIRONMENTAL POLICIES:\n"
        for policy in policies:
            message += f"  - {policy}\n"
        message += "\n"
    
    # List effects
    effects_dir = data_dir / "environmental_effects"
    if effects_dir.exists():
        pdf_effects = sorted(effects_dir.glob("*.pdf"))
        if pdf_effects:
            effects = sorted([f.stem.replace('_', ' ') for f in pdf_effects])
        else:
            effects = sorted([f.stem.replace('_', ' ') for f in effects_dir.glob("*.txt")])
        message += f"ENVIRONMENTAL EFFECTS & IMPACTS:\n"
        for effect in effects:
            message += f"  - {effect}\n"
        message += "\n"
    
    message += "Please ask about a specific policy or environmental effect from the lists above (e.g., 'Tell me about Carbon Pricing Mechanism' or 'What are the effects of Ocean Pollution?')."
    return message

def get_ambiguous_city(message: str):
    """Identify ambiguous city names referenced in the user message."""
    city_locations = build_city_country_map(
        pollution_tool.air_quality_data,
        weather_tool.weather_data,
    )
    return detect_ambiguous_city(message, city_locations)


def get_pollution_data(location: str) -> str:
    """Get air quality data for a location"""
    try:
        result = pollution_tool.get_air_quality(location)
        return result
    except Exception as e:
        return f"Error getting pollution data: {e}"

def calculate_carbon(activity: str, amount: str) -> str:
    """Calculate carbon emissions"""
    try:
        # Parse activity type
        if "car" in activity.lower() or "drive" in activity.lower():
            result = carbon_calc.calculate_transport_emissions("car", float(amount) if amount else 100)
        elif "flight" in activity.lower() or "fly" in activity.lower():
            result = carbon_calc.calculate_transport_emissions("flight", float(amount) if amount else 1000)
        elif "bus" in activity.lower():
            result = carbon_calc.calculate_transport_emissions("bus", float(amount) if amount else 100)
        elif "train" in activity.lower():
            result = carbon_calc.calculate_transport_emissions("train", float(amount) if amount else 100)
        elif "electricity" in activity.lower() or "energy" in activity.lower():
            result = carbon_calc.calculate_energy_emissions("electricity", float(amount) if amount else 100)
        elif "gas" in activity.lower() or "natural gas" in activity.lower():
            result = carbon_calc.calculate_energy_emissions("natural_gas", float(amount) if amount else 50)
        else:
            result = carbon_calc.calculate_transport_emissions("car", float(amount) if amount else 100)
        
        summary = result.get('summary', str(result))
        return f"**Carbon Calculation Results:**\n{summary}"
    except Exception as e:
        return f"Error calculating carbon: {e}"

def determine_tools(message: str) -> str:
    """Intelligently determine which tool(s) to use based on query content"""
    message_lower = (message or "").lower()

    # Keywords for different tools
    weather_keywords = ["weather", "temperature", "rain", "sunny", "cloudy", "storm", "snow", "wind"]
    weather_forecast_keywords = ["weather forecast", "weather prediction", "will it rain", "will it snow"]
    pollution_keywords = ["pollution", "air quality", "aqi", "pm2.5", "smog", "toxic", "health risk", "breathing", "pollutant", "air"]
    effects_keywords = ["effect", "effects", "impact", "impacts", "cause", "causes", "consequence", "consequences", "degradation"]
    forecast_keywords = ["long-term", "longterm", "long term", "yearly", "annual", "future", "predict", "projection", "2030", "2035", "years to come", "next decade", "trend"]
    carbon_keywords = ["carbon", "emissions", "footprint", "drive", "fly", "flight", "car", "transport", "vehicle", "energy use"]
    policy_keywords = [
        "policy", "regulation", "framework", "act", "law", "standard", "renewable", "solar", "wind", "climate plan", "goal",
        "superfund", "rcra", "tsca", "nepa", "clean water", "clean air", "endangered species",
        "pollution prevention", "waste management", "environmental justice", "inflation reduction", "cercla"
    ]

    # Check for long-term pollution/AQI forecast FIRST (before ambiguous city check,
    # since forecast data handles city lookup internally)
    has_forecast = any(keyword in message_lower for keyword in forecast_keywords)
    has_pollution = any(keyword in message_lower for keyword in pollution_keywords + ["pollution", "aqi", "air"])
    has_effects = any(keyword in message_lower for keyword in effects_keywords)
    has_realtime_air_intent = any(keyword in message_lower for keyword in ["today", "now", "current", "aqi", "pm2.5", "forecast"])
    if has_forecast and (has_pollution or any(k in message_lower for k in ["environment", "health index", "index"])):
        return "Pollution Forecast"

    # Effect/cause/impact questions should use RAG documents, even if they mention pollution.
    if has_effects and not has_realtime_air_intent:
        return "RAG Search"

    # "forecast" + pollution context → short-term Pollution Index (e.g. "pollution forecast for Seattle")
    if "forecast" in message_lower and has_pollution:
        return "Pollution Index"

    # Check for weather query BEFORE ambiguous city check
    # (weather tool handles location disambiguation internally)
    if any(keyword in message_lower for keyword in weather_keywords) or \
       any(phrase in message_lower for phrase in weather_forecast_keywords) or \
       "forecast" in message_lower:
        return "Weather"

    # Pre-check for ambiguous city names to prevent hallucination
    ambiguous_city, _ = get_ambiguous_city(message)
    if ambiguous_city:
        return "Ambiguous Location"

    # Check for pollution query
    if any(keyword in message_lower for keyword in pollution_keywords):
        return "Pollution Index"
    
    # Check for carbon query
    if any(keyword in message_lower for keyword in carbon_keywords):
        return "Carbon Calculator"
    
    # Check for policy query
    if any(keyword in message_lower for keyword in policy_keywords):
        return "RAG Search"
    
    # Default to smart query for comprehensive answer
    return "Smart Query"

def clean_response_for_chat(tool_results: dict, message: str) -> str:
    """Convert raw tool results into a clean, consolidated answer for the chat"""
    
    # Guard: ambiguous city -> ask for city/state/country instead of hallucinating
    ambiguous_city, ambiguous_countries = get_ambiguous_city(message)
    if ambiguous_city:
        formatted_countries = ', '.join(sorted(ambiguous_countries))
        return (
            f"The city '{ambiguous_city.title()}' appears in multiple regions ({formatted_countries}). "
            "Please include city, state, and country to ensure the correct location is used, e.g., "
            f"'{ambiguous_city.title()}, British Columbia, Canada' or '{ambiguous_city.title()}, Kansas, USA'."
        )

    # Extract and clean content from tool results
    if "weather_result" in tool_results:
        result = tool_results["weather_result"]
        # Return clean weather text directly
        return result

    if "pollution_result" in tool_results:
        # For pollution queries, provide a professional summary from AQI tool output
        result = tool_results["pollution_result"]

        if result.lower().startswith("i don't know"):
            return result

        lines = result.split('\n')
        clean_lines = [line.strip() for line in lines
                       if line.strip() and
                       '**Tools' not in line and
                       not any(x in line for x in ['relevance:', '[HEART]'])]

        if not clean_lines:
            return "I couldn't find current air quality data for that location. Please check the Logs tab for details."
        # Professional answer style
        answer_lines = []
        answer_lines.append("Assessment based on current environmental data:")
        answer_lines.append("\n".join(clean_lines[:6]))
        answer_lines.append("\nRecommendations: reduce outdoor exposure if pollution is high and use masks or indoor air filtration as appropriate.")

        return "\n".join(answer_lines)
    
    if "carbon_result" in tool_results:
        # For carbon queries, return the calculation results
        result = tool_results["carbon_result"]
        lines = result.split('\n')
        clean_lines = [line.strip() for line in lines if line.strip() and not any(x in line for x in ['**Carbon', '[HEART]'])]
        return '\n'.join(clean_lines[:8])
    
    if "rag_result" in tool_results or "web_result" in tool_results:
        # For smart queries or general questions, synthesize comprehensive answer
        rag_result = tool_results.get("rag_result", "")
        web_result = tool_results.get("web_result", "")
        message_lower = message.lower()
        policy_terms = [
            "policy", "regulation", "act", "law", "framework", "superfund", "rcra", "tsca", "nepa",
            "clean water", "clean air", "endangered species", "waste management", "cercla"
        ]
        is_policy_like_query = any(
            re.search(rf"\b{re.escape(term)}\b", message_lower) is not None
            for term in policy_terms
        )

        # Clean up RAG results - extract just meaningful content
        rag_lines = rag_result.split('\n')
        rag_content = []
        for line in rag_lines:
            line_clean = line.strip()
            # Skip empty lines, headers with symbols, relevance scores, and formatting markers
            if (line_clean and 
                not line_clean.startswith('📋') and 
                not line_clean.startswith('🌍') and 
                not line_clean.startswith('■') and
                not line_clean.startswith('●') and
                'relevance' not in line_clean.lower() and
                'Environmental Policies:' not in line_clean and
                'Environmental Effects:' not in line_clean and
                not line_clean.startswith('Error searching RAG:')):
                rag_content.append(line_clean)
        
        # Clean up web results
        web_lines = web_result.split('\n')
        web_content = []
        for line in web_lines:
            line_clean = line.strip()
            if (line_clean and 
                'Web Search Results:' not in line_clean and
                'Environmental News' not in line_clean and
                '1.' not in line_clean[:5] and
                line_clean != 'Environmental News'):
                web_content.append(line_clean)
        
        # Build consolidated answer
        final_answer = []
        
        if web_content and any(keyword in message.lower() for keyword in ['weather', 'temperature', 'climate']):
            # Prioritize web results for weather questions
            final_answer.extend(web_content[:3])
        elif is_policy_like_query and rag_content:
            # For policy questions, always prioritize document-backed policy content.
            intro = "Based on the USA environmental policy documents in this system:"
            final_answer.append(intro)
            final_answer.extend(rag_content[:4])
        elif web_content:
            # Include web content first for general questions
            final_answer.extend(web_content[:2])
        
        if rag_content and not is_policy_like_query:
            # Add environmental knowledge
            final_answer.extend(rag_content[:3])
        
        if final_answer:
            return '\n'.join(final_answer)
        else:
            return "I found relevant environmental information about your query. Please check the Logs tab for detailed sources."
    
    return "I've processed your question. Check the Logs tab for detailed information."

def synthesize_response(tool_name: str, message: str, tool_results: dict) -> str:
    """Synthesize tool results into a cohesive, well-structured answer"""
    
    if tool_name == "RAG Search":
        # Create clean version for chat
        clean_answer = clean_response_for_chat(tool_results, message)
        return clean_answer if clean_answer else "Based on our environmental database, I found relevant information about your query. Please see the Logs tab for detailed sources."
    
    elif tool_name == "Pollution Index":
        pollution_result = tool_results.get("pollution_result", "No air quality data available.")
        # Extract clean lines
        lines = [l.strip() for l in pollution_result.split('\n') if l.strip()]
        return '\n'.join(lines[:8])

    elif tool_name == "Pollution Forecast":
        forecast_result = tool_results.get("forecast_result", "No forecast data available.")
        lines = [l.strip() for l in forecast_result.split('\n') if l.strip()]
        return '\n'.join(lines)
    
    elif tool_name == "Carbon Calculator":
        carbon_result = tool_results.get("carbon_result", "Carbon calculator ready.")
        # Extract clean lines
        lines = [l.strip() for l in carbon_result.split('\n') if l.strip()]
        return '\n'.join(lines[:8])
    
    elif tool_name == "Smart Query":
        # Use the clean response function for consolidated answer
        return clean_response_for_chat(tool_results, message)
    
    return "Unable to generate response."

def chatbot_response(message: str) -> tuple:
    """Generate chatbot response with intelligent tool selection and synthesis"""
    
    global conversation_history
    
    # Store message in history
    conversation_history.append({"user": message, "timestamp": datetime.now().isoformat()})
    
    response = ""
    tools_used = []
    tool_results = {}

    ambiguous_city, ambiguous_countries = get_ambiguous_city(message)
    
    try:
        # Intelligently determine which tool to use
        mode = determine_tools(message)

        if mode == "Ambiguous Location":
            response = format_ambiguity_prompt(ambiguous_city, ambiguous_countries)
            tools_used = []

        elif mode == "RAG Search":
            rag_result = rag_search(message)
            tool_results["rag_result"] = rag_result
            tools_used.append("RAG Retrieval")
            response = synthesize_response("RAG Search", message, tool_results)
        
        elif mode == "Weather":
            # Extract location from message
            if "for " in message.lower():
                location = message.lower().split("for ")[-1].strip()
            elif "in " in message.lower():
                location = message.lower().split("in ")[-1].strip()
            else:
                location = message.strip()

            # Clean trailing punctuation and common words
            location = location.strip(" .?!")
            trailing_words = ["today", "now", "please", "right", "currently", "at", "on", "in", "time", "weather"]
            for word in trailing_words:
                if location.lower().endswith(" " + word):
                    location = location.rsplit(" ", 1)[0].strip()

            weather_result = weather_tool.get_weather(location)
            tool_results["weather_result"] = weather_result
            tools_used.append("Weather Tool")
            response = clean_response_for_chat(tool_results, message)

        elif mode == "Pollution Index":
            # Extract location from message
            if "for " in message.lower():
                location = message.lower().split("for ")[-1].strip()
            elif "in " in message.lower():
                location = message.lower().split("in ")[-1].strip()
            else:
                location = message.strip()
            
            # Clean trailing punctuation and common words
            location = location.strip(" .?!")
            trailing_words = ["today", "now", "please", "right", "currently", "at", "on", "in", "time", "weather", "report", "data"]
            for word in trailing_words:
                if location.lower().endswith(" " + word):
                    location = location.rsplit(" ", 1)[0].strip()

            pollution_result = get_pollution_data(location)
            tool_results["pollution_result"] = pollution_result
            tools_used.append("Pollution Index Tool")
            response = synthesize_response("Pollution Index", message, tool_results)

        elif mode == "Pollution Forecast":
            # Extract location from message
            if "for " in message.lower():
                location = message.lower().split("for ")[-1].strip()
            elif "in " in message.lower():
                location = message.lower().split("in ")[-1].strip()
            elif "of " in message.lower():
                location = message.lower().split("of ")[-1].strip()
            else:
                location = message.strip()

            location = location.strip(" .?!")
            trailing_words = ["today", "now", "please", "forecast", "prediction", "projection", "trend", "years", "decade"]
            for word in trailing_words:
                if location.lower().endswith(" " + word):
                    location = location.rsplit(" ", 1)[0].strip()

            forecast_result = pollution_tool.get_longterm_forecast(location)
            tool_results["forecast_result"] = forecast_result
            tools_used.append("Pollution Forecast Tool")
            response = synthesize_response("Pollution Forecast", message, tool_results)
        
        elif mode == "Carbon Calculator":
            # Try to extract activity and amount from message
            parts = message.split()
            activity = ' '.join(parts[:2]) if len(parts) >= 2 else "car"
            amount = parts[-1] if parts[-1].replace('.', '', 1).isdigit() else "100"
            
            carbon_result = calculate_carbon(activity, amount)
            tool_results["carbon_result"] = carbon_result
            tools_used.append("Carbon Calculator")
            response = synthesize_response("Carbon Calculator", message, tool_results)
        
        elif mode == "Smart Query":
            # Use multiple tools for comprehensive answer
            rag_result = rag_search(message)
            web_result = web_search.search(message)
            
            tool_results["rag_result"] = rag_result
            tool_results["web_result"] = web_result
            tools_used = ["RAG Retrieval", "Web Search"]
            response = synthesize_response("Smart Query", message, tool_results)
    
    except Exception as e:
        response = f"I apologize for the difficulty. While processing your query, I encountered an issue: {str(e)}. Please try asking your question in a different way, or provide more specific details."
        tools_used.append("Error Handler")
    
    # Add to history
    conversation_history[-1]["response"] = response

    conversation_history[-1]["tools"] = tools_used
    
    # Add environmental health quote at top of response (NO TOOL INFO)
    quote = random.choice(environmental_quotes)
    response_with_quote = f"**Quote for you:**\n{quote}\n\nHello,\n\n{response}"
    
    # Build tool details display for Logs tab
    tool_info = f"**Tools Used:** {', '.join(tools_used)}\n\n"
    tool_info += "**Tool Details:**\n"
    for tool_name, result in tool_results.items():
        tool_info += f"\n**{tool_name.upper()}:**\n{result}\n---\n"
    
    # Build query history display
    history_text = "**Query History:**\n\n"
    for i, h in enumerate(conversation_history, 1):
        time_str = h['timestamp'].split('T')[1][:5] if 'timestamp' in h else ""
        history_text += f"{i}. [{time_str}] Q: {h['user']}\n"
        if 'tools' in h:
            history_text += f"   Tools: {', '.join(h['tools'])}\n"
        history_text += "\n"
    
    return response_with_quote, tool_info, history_text

# Build Gradio Interface
with gr.Blocks(title="GreenMind - Agentic RAG") as demo:
    
    with gr.Tabs():
        
        # ===== CHAT TAB =====
        with gr.TabItem("Chat", id="chat_tab"):
            gr.Markdown("## Welcome to GreenMind\nYour Environmental Health Advisor")
            
            with gr.Row():
                with gr.Column(scale=3):
                    user_input = gr.Textbox(
                        label="Ask about environmental topics",
                        placeholder="E.g., 'What's the carbon footprint of flying?' or 'Tell me about renewable energy policies' or 'What's the air quality in Seattle?'",
                        lines=3
                    )
                    
                    send_btn = gr.Button("Get Answer", variant="primary", scale=1)
            
            with gr.Row():
                response_output = gr.Markdown(label="Response")
            
            with gr.Row():
                history_output = gr.Textbox(
                    label="Recent History",
                    lines=5,
                    interactive=False
                )
        
        # ===== LOGS TAB =====
        with gr.TabItem("Logs", id="logs_tab"):
            gr.Markdown("## Query Details & Tool Information")
            
            with gr.Row():
                logs_output = gr.Textbox(
                    label="Tool Details & Query Analysis",
                    lines=15,
                    interactive=False
                )
        
        # ===== ABOUT TAB =====
        with gr.TabItem("About", id="about_tab"):
            gr.Markdown("""
            ## About GreenMind
            
            GreenMind is an **Agentic RAG System** designed to provide intelligent sustainability advice 
            using cutting-edge AI and environmental knowledge.
            
            ### Key Features
            
            - **RAG Retrieval**: Access to 134+ environmental documents
            - **Multi-Tool AI**: Combines multiple specialized tools for comprehensive answers
            - **Real-time Data**: Web search for latest environmental news
            - **Environmental Health Focus**: All guidance includes health impact analysis
            
            ### How It Works
            
            1. **Your Question** -> 2. **Agent Analyzes** -> 3. **Tools Execute** -> 4. **Smart Synthesis** -> 5. **Your Answer**
            
            The system uses:
            - **Vector Database (FAISS)**: Semantic document search with 384-dim embeddings
            - **Sentence Transformers**: all-MiniLM-L6-v2 model for understanding similarity
            - **Web Search**: Current environmental data and news
            - **Policy Analysis**: Access to 64+ environmental policy documents
            - **Effects Database**: 70+ documents on environmental effects on health
            
            ### Query Modes Explained
            
            | Mode | What It Does |
            |------|------------|
            | **Smart Query** | Combines RAG + Web Search for comprehensive analysis |
            | **RAG Search** | Searches your indexed environmental documents |
            | **Pollution Index** | Gets air quality data for specific locations |
            | **Carbon Calculator** | Calculates personal/organizational carbon footprint |
            
            ### Sample Questions to Try
            
            - "What are the environmental effects of climate change?"
            - "How does renewable energy policy work?"
            - "What's the air quality in [city name]?"
            - "How many tons of CO2 does a flight produce?"
            - "Tell me about circular economy frameworks"
            - "What are the health impacts of air pollution?"
            
            ---
            """)
            
            # System Info
            with gr.Accordion("System Statistics", open=False):
                stats = vector_db.get_stats()
                doc_count = sum(v.get('doc_count', 0) for v in stats['metadata'].values())
                sources_list = ', '.join(stats['metadata'].keys())
                
                gr.Markdown(f"""
                ### Vector Database Stats
                
                - **Total Indexed Documents**: {doc_count}
                - **Document Sources**: {sources_list}
                - **Embedding Model**: Sentence Transformers (all-MiniLM-L6-v2)
                - **Vector Dimensions**: 384
                - **Index Type**: FAISS (Fast Approximate Similarity Search)
                - **Database Path**: `vector_db/faiss_index/`
                
                ### Available Tools
                
                1. **RAG Document Retrieval** - Search 134+ environmental documents
                2. **Web Search Tool** - Current environmental news and data
                3. **Pollution Index Tool** - Real-time air quality information
                4. **Carbon Calculator** - Emission footprint calculations
                
                ### Technical Stack
                
                - **Framework**: LangChain 0.1.11
                - **UI**: Gradio (Python 3.14 compatible)
                - **Vector DB**: FAISS 1.7.4
                - **Embeddings**: Sentence Transformers
                - **Search**: SerpAPI + Simulated Data
                - **Logging**: JSON-structured session logs
                """)
            
            # Environmental Health Focus
            with gr.Accordion("Why Environmental Health?", open=False):
                gr.Markdown("""
                ### Health-Environment Connection
                
                GreenMind specifically focuses on **environmental health** because:
                
                #### Key Facts
                
                - **7 million deaths/year** from air pollution alone
                - **2 billion people** facing water scarcity affecting health
                - **Climate change** increases disease spread and health crises
                - **Pollution** costs **$6+ trillion annually** in health care
                
                #### Our Mission
                
                Every recommendation in GreenMind considers:
                
                1. **Air Quality Impact** - How decisions affect respiratory health
                2. **Water Safety** - Clean water access for communities
                3. **Food Security** - Sustainable agriculture for nutrition
                4. **Biodiversity** - Ecosystem services for human wellbeing
                5. **Climate Action** - Long-term health protection
                
                #### Guiding Principles
                
                - No environmental solution is complete without health benefit
                - Vulnerable populations deserve priority attention
                - Scientific evidence guides all recommendations
                - Local communities lead sustainability initiatives
                """)
            
            # Developer Info
            with gr.Accordion("Technical Details", open=False):
                gr.Markdown(f"""
                ### Project Information
                
                - **Project Type**: Capstone - Agentic RAG System
                - **Date Deployed**: April 2, 2026
                - **Python Version**: 3.14.3
                - **Database Engine**: FAISS Vector DB
                - **Status**: Production Ready
                
                ### Architecture
                
                ```
                User Query
                    ↓
                Agent Orchestrator
                    ↓
                [Tool Selection]
                    ↓
                ┌─────────────────────────────────────┐
                │  RAG  │  Web Search  │  Tools       │
                └─────────────────────────────────────┘
                    ↓
                LLM (with health focus)
                    ↓
                Comprehensive Answer
                    ↓
                Logging & Analytics
                ```
                
                ### Data Sources
                
                **Environmental Policies** (64 chunks):
                - Climate Action Plan 2024
                - Renewable Energy Act
                - Carbon Pricing Mechanism
                - Circular Economy Framework
                - And 6 more policy documents
                
                **Environmental Effects** (70 chunks):
                - Climate Change Impact Report
                - Ocean Pollution Effects
                - Air Quality Degradation
                - Health Impact Analysis
                - And 6 more effects documents
                """)
    
    # Event handling
    send_btn.click(
        fn=chatbot_response,
        inputs=[user_input],
        outputs=[response_output, logs_output, history_output]
    )
    
    # Allow Enter key to send
    user_input.submit(
        fn=chatbot_response,
        inputs=[user_input],
        outputs=[response_output, logs_output, history_output]
    )

if __name__ == "__main__":
    def find_available_port(start_port: int = 7861, max_attempts: int = 30) -> int:
        """Return the first free TCP port in [start_port, start_port + max_attempts)."""
        for port in range(start_port, start_port + max_attempts):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                if sock.connect_ex(("127.0.0.1", port)) != 0:
                    return port
        raise OSError(f"No free port found in range {start_port}-{start_port + max_attempts - 1}")

    preferred_port = int(os.getenv("GRADIO_SERVER_PORT", "7861"))
    launch_port = find_available_port(preferred_port)

    print("\n" + "="*70)
    print("GreenMind Agentic RAG - Gradio Web Interface")
    print("="*70)
    print("\nStarting web server...\n")
    print(f"Open your browser to: http://localhost:{launch_port}")
    print("\nPress Ctrl+C to stop the server\n")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=launch_port,
        share=False,
        show_error=True,
        theme=gr.themes.Soft(),
    )
