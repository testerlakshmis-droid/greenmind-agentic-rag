# Streamlit UI for GreenMind Agent

import streamlit as st
import time
from datetime import datetime
import os
import sys

# Add parent directory to path to import src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.green_agent import GreenMindAgent

# Page configuration
st.set_page_config(
    page_title="GreenMind - Sustainability Advisor",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        color: #2d5016;
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .tool-badge {
        display: inline-block;
        padding: 5px 10px;
        margin: 5px 5px 5px 0;
        background-color: #81c784;
        color: white;
        border-radius: 20px;
        font-size: 12px;
    }
    .response-box {
        padding: 15px;
        border-radius: 8px;
        background-color: #f1f8e9;
        border-left: 4px solid #558b2f;
    }
    .query-box {
        padding: 15px;
        border-radius: 8px;
        background-color: #e3f2fd;
        border-left: 4px solid #1565c0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
    st.session_state.messages = []
    st.session_state.agent_initialized = False

def initialize_agent():
    """Initialize GreenMind Agent"""
    try:
        st.session_state.agent = GreenMindAgent()
        st.session_state.agent_initialized = True
        st.session_state.messages = []
        return True
    except Exception as e:
        st.error(f"Failed to initialize agent: {str(e)}")
        return False

def format_tool_badges(tools):
    """Format tool usage as badges"""
    if not tools:
        return "No tools used"
    
    html = "Tools used: "
    for tool in tools:
        tool_name = tool.replace('_', ' ').title()
        html += f'<span class="tool-badge">{tool_name}</span>'
    
    return html

# Main header
st.markdown("""
    <div class="main-header">
        <h1>🌍 GreenMind - Intelligent Sustainability Advisor</h1>
        <p><i>Your AI companion for environmental knowledge and sustainable living</i></p>
    </div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    if not st.session_state.agent_initialized:
        if st.button("🚀 Initialize GreenMind", key="init_btn"):
            with st.spinner("Initializing agent..."):
                if initialize_agent():
                    st.success("Agent initialized successfully!")
                    st.rerun()
    else:
        st.markdown("✅ **Agent Status**: Ready")
        
        # Display session info
        st.markdown("---")
        st.markdown("### 📊 Session Information")
        
        if st.session_state.agent:
            session_summary = st.session_state.agent.get_session_summary()
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Session ID", session_summary['session_id'][:8] + "...")
            
            with col2:
                st.metric("Messages", session_summary['total_interactions'])
        
        # About section
        st.markdown("---")
        st.markdown("### 📚 About GreenMind")
        st.markdown("""
        GreenMind is an Agentic RAG system that provides:
        - Environmental policy information
        - Climate change and effects analysis
        - Current environmental news and initiatives
        - Air quality and pollution data
        - Carbon footprint calculations
        """)

# Main content area
if not st.session_state.agent_initialized:
    st.info("👈 Click 'Initialize GreenMind' in the sidebar to get started!")
else:
    # Display previous messages
    st.markdown("### 💬 Conversation")
    
    for message in st.session_state.messages:
        if message['role'] == 'user':
            st.markdown(f'<div class="query-box"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="response-box"><strong>GreenMind:</strong> {message["content"]}</div>', unsafe_allow_html=True)
            
            if message.get('tools_used'):
                st.markdown(format_tool_badges(message['tools_used']), unsafe_allow_html=True)
            
            if message.get('processing_time_ms'):
                st.caption(f"⏱️ Response time: {message['processing_time_ms']}ms")
    
    # Input section
    st.markdown("---")
    st.markdown("### 🎯 Ask GreenMind")
    
    # User input
    user_input = st.text_area(
        "Your question about environmental topics:",
        placeholder="e.g., 'What are the latest renewable energy policies?' or 'Tell me about the air quality in Delhi'",
        height=100,
        key="user_input"
    )
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        send_button = st.button("Send 📤", key="send_btn")
    
    with col2:
        clear_button = st.button("Clear 🗑️", key="clear_btn")
    
    # Handle send button
    if send_button and user_input.strip():
        # Add user message to history
        st.session_state.messages.append({
            'role': 'user',
            'content': user_input
        })
        
        # Get response from agent
        with st.spinner("GreenMind is thinking..."):
            try:
                response = st.session_state.agent.chat(user_input)
                
                # Add agent response to history
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': response['answer'],
                    'tools_used': response.get('tools_used', []),
                    'processing_time_ms': response.get('processing_time_ms', 0)
                })
                
                # Clear input
                st.rerun()
            
            except Exception as e:
                st.error(f"Error getting response: {str(e)}")
    
    # Handle clear button
    if clear_button:
        st.session_state.messages = []
        st.rerun()
    
    # Export logs button
    if st.button("📥 Download Logs", key="download_btn"):
        try:
            st.session_state.agent.save_logs()
            st.success("Logs saved to logs directory!")
        except Exception as e:
            st.error(f"Error saving logs: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px;">
    <p>GreenMind v1.0 | Powered by LangChain & Google Gemini | © 2024</p>
    <p>Committed to environmental sustainability through intelligent technology</p>
</div>
""", unsafe_allow_html=True)
