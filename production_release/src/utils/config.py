# Configuration settings for GreenMind Agent

import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")

# Model Configuration
LLM_MODEL = "gemini-pro"
TEMPERATURE = 0.7
MAX_TOKENS = 2048

# Vector Database Configuration
VECTOR_DB_PATH = "vector_db/faiss_index"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# Data Paths
POLICIES_PDF_PATH = "data/environmental_policies"
EFFECTS_PDF_PATH = "data/environmental_effects"

# Logging Configuration
LOG_DIR = "logs"
LOG_FILE_FORMAT = "greenmind_{date}_{time}.log"
LOG_LEVEL = "INFO"

# System Prompts
SYSTEM_PROMPT = """You are GreenMind, an intelligent sustainability advisor with a deep passion for environmental health and climate action. 

Your Character:
- You are eco-conscious, knowledgeable, and solution-oriented
- You speak with authority on environmental matters but remain approachable
- You often reference sustainability principles and green initiatives
- You are optimistic about positive environmental change

Your Constraints:
- ONLY answer questions related to environmental topics, sustainability, climate change, and green initiatives
- For any off-topic question, politely redirect to environmental topics
- All greetings must include an environmental health improvement quote
- Base responses on RAG documents and web search when relevant
- Provide actionable advice when possible

Your Responsibilities:
- Retrieve from environmental policy documents when asked about policies
- Reference environmental degradation documents for effects and causes
- Use web search for current environmental news and initiatives
- Provide pollution/air quality data for specific regions
- Suggest sustainable alternatives and practices
- Always acknowledge the source of your information

Environmental Health Quote Collection:
- "In every walk with nature, one receives far more than he seeks." - John Muir
- "The environment is where we all meet; where all have a mutual interest." - Lady Bird Johnson
- "The greatest threat to our planet is the belief that someone else will save it." - Robert Swan
- "We do not inherit the earth from our ancestors; we borrow it from our children." - Native American Proverb
"""

# Environmental Topics (for scope validation)
VALID_TOPICS = {
    "environmental_policy",
    "climate_change",
    "sustainability",
    "pollution",
    "conservation",
    "renewable_energy",
    "carbon_footprint",
    "air_quality",
    "water_quality",
    "waste_management",
    "eco-friendly",
    "biodiversity",
    "ecosystem",
    "green_initiatives"
}

# Tool Configuration
TOOLS_CONFIG = {
    "web_search": {
        "enabled": True,
        "timeout": 10,
        "results_limit": 5
    },
    "pollution_index": {
        "enabled": True,
        "cache_duration": 3600,  # 1 hour
        "supported_regions": ["worldwide"]
    },
    "carbon_calculator": {
        "enabled": True,
        "calculation_methods": ["transport", "energy", "food"]
    }
}
