import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import requests
import json
import warnings
import os
import re
import sys
import asyncio
import tempfile
import io

# Handle environment variables for both local and Streamlit Cloud
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load from .env file if running locally
except ImportError:
    # dotenv not available (e.g., on Streamlit Cloud)
    pass

warnings.filterwarnings('ignore')

# Helper function to get environment variables from either .env or Streamlit secrets
def get_env_var(key, default=None):
    """Get environment variable from .env file (local) or Streamlit secrets (cloud)"""
    # First try regular environment variables (from .env or system)
    value = os.getenv(key)
    if value:
        return value

    # Then try Streamlit secrets (for Streamlit Cloud deployment)
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    return default

# Page configuration
st.set_page_config(
    page_title="AI-Powered CSV Data Analyzer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application"""
    st.markdown('<h1 class="main-header">🤖 AI-Powered CSV Data Analyzer v3.0</h1>', unsafe_allow_html=True)
    
    st.markdown("## ✨ Welcome to the Stable Release!")
    st.info("This is a production-ready version with comprehensive testing and deployment configurations.")
    
    # Features overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Core Features")
        st.markdown("- **AI-Powered CSV Analysis**")
        st.markdown("- **Business Contact Research**")
        st.markdown("- **Email Campaign Management**")
        st.markdown("- **Data Visualization**")
    
    with col2:
        st.markdown("### 🔧 Technical Features")
        st.markdown("- **Multiple Email Providers**")
        st.markdown("- **Web Scraping Integration**")
        st.markdown("- **Testing Framework**")
        st.markdown("- **Production Deployment**")
    
    # Setup instructions
    st.markdown("---")
    st.markdown("### 🚀 Quick Setup")
    
    st.code("""
# 1. Clone the repository
git clone https://github.com/MyWinwood/ai-csv-business-analyzer-stable-v3.git

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 4. Run the application
streamlit run ai_csv_analyzer.py
    """, language="bash")
    
    # Testing instructions
    st.markdown("### 🧪 Testing")
    
    st.code("""
# Enable testing dependencies
# Uncomment pytest>=7.0.0 in requirements.txt

# Install pytest
pip install pytest

# Run all tests
python -m pytest tests/ -v
    """, language="bash")
    
    # API keys status
    st.markdown("### 🔑 API Configuration Status")
    
    groq_key = get_env_var('GROQ_API_KEY')
    tavily_key = get_env_var('TAVILY_API_KEY')
    openai_key = get_env_var('OPENAI_API_KEY')
    
    col_api1, col_api2, col_api3 = st.columns(3)
    
    with col_api1:
        if groq_key and len(groq_key) > 10:
            st.success("✅ Groq API: Configured")
        else:
            st.warning("⚠️ Groq API: Not configured")
    
    with col_api2:
        if tavily_key and len(tavily_key) > 10:
            st.success("✅ Tavily API: Configured") 
        else:
            st.warning("⚠️ Tavily API: Not configured")
    
    with col_api3:
        if openai_key and len(openai_key) > 10:
            st.success("✅ OpenAI API: Configured")
        else:
            st.info("ℹ️ OpenAI API: Optional")

    # Repository information
    st.markdown("---")
    st.markdown("### 🔗 Repository Information")
    
    st.markdown("""
    **Repository URL**: https://github.com/MyWinwood/ai-csv-business-analyzer-stable-v3
    
    **Version**: 3.0 Stable Release
    
    **Features**:
    - ✅ Comprehensive AI data analysis
    - ✅ Email campaign management
    - ✅ Business contact research  
    - ✅ Full test coverage
    - ✅ Production deployment ready
    """)

if __name__ == "__main__":
    main()
