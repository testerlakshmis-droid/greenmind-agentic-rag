# GreenMind Agentic RAG - Copilot Instructions

## Project Overview
GreenMind is an Agentic RAG system designed to provide intelligent sustainability advice using:
- LangChain framework
- Google Gemini API
- FAISS vector database
- Streamlit UI
- Multiple tools for environmental data and policies

## key Features
- RAG tools for environmental policies and effects
- Web search capabilities
- Air quality and pollution index tracking
- Character-driven assistant personality
- Comprehensive logging system

## Development Guidelines
- Follow PEP 8 for Python code
- Use environment variables for API keys
- Maintain consistent logging across all tools
- Test RAG retrieval quality before deployment

## Project Structure
```
CapstoneProject/
├── .github/
├── src/
│   ├── agent/
│   ├── tools/
│   ├── rag/
│   └── ui/
├── data/
│   ├── environmental_policies/
│   └── environmental_effects/
├── config/
├── logs/
├── vector_db/
├── requirements.txt
└── README.md
```
