# GreenMind - Intelligent Sustainability Advisor

An Agentic RAG system powered by LangChain and Google Gemini that provides environmental sustainability advice using multiple tools and data sources.

## Features

### Core Components
1. **Environmental Policies RAG Tool** - Access to 10+ government environmental policy documents
2. **Environmental Effects RAG Tool** - Knowledge base of 10+ documents on environmental degradation and effects
3. **Web Search Tool** - Real-time information on environmental policies and current affairs
4. **Pollution Index Tool** - Current air quality data and forecasts for countries/states/cities
5. **Additional Tools** - Carbon footprint calculator, sustainability recommendations engine

### System Characteristics
- **Personality-Driven**: GreenMind has a distinct character and perspective on environmental issues
- **Scope-Limited**: Only responds to environment-related queries
- **Eco-Conscious Greetings**: All greetings include environmental health improvement quotes
- **Comprehensive Logging**: Detailed logs of all tool usage and responses
- **Modern UI**: Streamlit-based user interface for easy interaction

## Technology Stack

| Component | Technology |
|-----------|-----------|
| **Framework** | LangChain |
| **LLM** | Google Gemini |
| **Vector Database** | FAISS |
| **UI** | Streamlit |
| **Language** | Python 3.8+ |

## Project Structure

```
CapstoneProject/
├── .github/
│   └── copilot-instructions.md
├── src/
│   ├── agent/
│   │   ├── __init__.py
│   │   └── green_agent.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── web_search_tool.py
│   │   ├── pollution_index_tool.py
│   │   ├── carbon_calculator.py
│   │   └── fact_checker.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── document_processor.py
│   │   ├── vector_db.py
│   │   └── retrieval.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── streamlit_app.py
│   │   └── components.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── config.py
├── data/
│   ├── environmental_policies/  (10+ PDF files)
│   └── environmental_effects/   (10+ PDF files)
├── config/
│   └── config.yaml
├── logs/
│   └── (generated dynamically)
├── vector_db/
│   └── (FAISS index storage)
├── requirements.txt
└── README.md
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup Steps

1. **Clone/Setup Project**
   ```bash
   cd c:\Users\Murali\Desktop\CapstoneProject
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   ```bash
   # Create .env file in project root
   GOOGLE_API_KEY=your_api_key_here
   SERPAPI_API_KEY=your_serpapi_key_here  # Optional, for web search
   ```

5. **Add Sample PDFs**
   - Place environmental policy PDFs in `data/environmental_policies/` (minimum 10 files)
   - Place environmental effects PDFs in `data/environmental_effects/` (minimum 10 files)

6. **Initialize Vector Database**
   ```bash
   python -m src.rag.vector_db --initialize
   ```

7. **Run Application**
   ```bash
   streamlit run src/ui/streamlit_app.py
   ```

## Usage

### Starting the Application
```bash
streamlit run src/ui/streamlit_app.py
```

The application will:
1. Load environment policies and effects from PDFs
2. Build/load FAISS vector index
3. Initialize the GreenMind agent with all tools
4. Start the Streamlit interface on `http://localhost:8501`

### Interacting with GreenMind

1. **Ask Environmental Questions**: Query the agent about environmental policies, sustainability, climate change, etc.
2. **Request Current Information**: Get real-time data on air quality, pollution levels, recycling programs
3. **Get Recommendations**: Receive personalized sustainability advice
4. **View Logs**: Check tool usage and response details in the logs directory

## Tool Descriptions

### Environmental Policies RAG
Retrieves information from government environmental policy documents

### Environmental Effects RAG
Provides knowledge on environmental degradation, causes, and effects

### Web Search Tool
Searches current information about environmental news and policies

### Pollution Index Tool
Queries real-time air quality data and provides forecasts

### Carbon Calculator
Estimates carbon footprint based on user inputs

### Fact Checker
Verifies environmental claims and facts

## Logging

All interactions are logged to `logs/` directory with:
- Timestamp of each query
- Tools used
- Tool responses
- Final agent response
- Processing time

Log format: `greenmind_[date]_[time].log`

## API Keys Required

1. **Google Gemini API** - For LLM functionality
   - Get from: https://makersuite.google.com/app/apikey

2. **Optional - SerpAPI** - For web search
   - Get from: https://serpapi.com

## Performance Optimization

- Vector database caching
- Response streaming
- Batch PDF processing
- Intelligent prompt engineering

## Troubleshooting

### Vector Database Issues
```bash
# Rebuild vector database
python -m src.rag.vector_db --rebuild
```

### API Key Errors
- Verify `.env` file exists with correct API keys
- Check Google Gemini API quota

### PDF Loading Issues
- Ensure PDFs are in correct directories
- Check PDF file permissions
- Verify PDF format compatibility

## Future Enhancements

- Multi-language support
- Custom fine-tuning on environmental data
- Real-time satellite imagery integration
- Mobile app version
- Community contribution system

## References

- [Environmental Policy Guide](https://www.trp.org.in/)
- [WHO Environmental Health](https://www.who.int/)
- [LangChain Documentation](https://python.langchain.com/)
- [Google Gemini API](https://makersuite.google.com/)
- [FAISS Documentation](https://faiss.ai/)

## License

Academic Project - All Rights Reserved

## Support

For issues or questions, refer to the project logs and debugging section.

---

**Last Updated**: April 2026
**Version**: 1.0.0
