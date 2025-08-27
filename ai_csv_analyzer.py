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

# Import web scraping module
from modules.web_scraping_module import perform_web_scraping

# Import simplified data explorer
from data_explorer_new import create_data_explorer

# Import CSV research integration module
try:
    from modules.csv_research_integrator import add_csv_integration_interface, show_integration_status_sidebar
except ImportError:
    add_csv_integration_interface = None
    show_integration_status_sidebar = None
    print("CSV Integration module not found. Integration features disabled.")

# Import preprocessing utilities
try:
    from preprocessing_utils import show_preprocessing_interface, show_preprocessing_summary
except ImportError:
    show_preprocessing_interface = None
    show_preprocessing_summary = None
    print("Preprocessing utilities not found. Preprocessing features disabled.")

warnings.filterwarnings('ignore')

# Helper function to get environment variables from either .env or Streamlit secrets
def get_env_var(key, default=None):
    """Get environment variable from either .env file or Streamlit secrets"""
    # First try to get from environment
    value = os.getenv(key)
    if value:
        return value
    
    # Then try from Streamlit secrets if available
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    
    return default

def main():
    st.set_page_config(
        page_title="AI CSV Business Analyzer",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("📊 AI CSV Business Analyzer")
    st.markdown("---")

    # Initialize session state for data
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'original_df' not in st.session_state:
        st.session_state.original_df = None

    # Sidebar navigation
    st.sidebar.title("📋 Navigation")
    
    # Main tabs
    tabs = ["📤 Data Upload", "📊 Data Explorer", "🔍 Business Research", "🎯 CSV Integration"]
    
    # Check if preprocessing module is available
    if show_preprocessing_interface:
        tabs.append("🔧 Data Preprocessing")
    
    selected_tab = st.sidebar.radio("Select a feature:", tabs)

    # Add integration status sidebar if available
    if show_integration_status_sidebar:
        show_integration_status_sidebar()

    if selected_tab == "📤 Data Upload":
        st.header("📤 Upload Your CSV File")
        
        uploaded_file = st.file_uploader(
            "Choose a CSV file", 
            type="csv",
            help="Upload a CSV file to analyze business data"
        )
        
        if uploaded_file is not None:
            try:
                # Read the CSV file
                df = pd.read_csv(uploaded_file)
                st.session_state.df = df
                st.session_state.original_df = df.copy()
                
                st.success(f"✅ File uploaded successfully! {len(df)} rows and {len(df.columns)} columns loaded.")
                
                # Show basic info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Rows", len(df))
                with col2:
                    st.metric("Total Columns", len(df.columns))
                with col3:
                    st.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")
                
                # Preview the data
                st.subheader("📋 Data Preview")
                st.dataframe(df.head(10))
                
                # Show column information
                st.subheader("📝 Column Information")
                col_info = pd.DataFrame({
                    'Column': df.columns,
                    'Data Type': df.dtypes,
                    'Non-Null Count': df.count(),
                    'Null Count': df.isnull().sum(),
                    'Unique Values': [df[col].nunique() for col in df.columns]
                })
                st.dataframe(col_info)
                
            except Exception as e:
                st.error(f"❌ Error reading the CSV file: {str(e)}")
        else:
            st.info("📂 Please upload a CSV file to get started.")

    elif selected_tab == "📊 Data Explorer" and st.session_state.df is not None:
        create_data_explorer(st.session_state.df)
    
    elif selected_tab == "🔍 Business Research":
        st.header("🔍 Business Research & Data Enhancement")
        
        if st.session_state.df is None:
            st.warning("⚠️ Please upload a CSV file first in the 'Data Upload' tab.")
        else:
            # Show the web scraping interface
            perform_web_scraping(st.session_state.df)
    
    elif selected_tab == "🎯 CSV Integration" and add_csv_integration_interface:
        st.header("🎯 CSV Research Integration")
        
        if st.session_state.df is None:
            st.warning("⚠️ Please upload a CSV file first in the 'Data Upload' tab.")
        else:
            # Show the CSV integration interface
            add_csv_integration_interface(st.session_state.df)
    
    elif selected_tab == "🔧 Data Preprocessing" and show_preprocessing_interface:
        st.header("🔧 Data Preprocessing")
        
        if st.session_state.df is None:
            st.warning("⚠️ Please upload a CSV file first in the 'Data Upload' tab.")
        else:
            # Show preprocessing interface
            processed_df = show_preprocessing_interface(st.session_state.df)
            if processed_df is not None:
                st.session_state.df = processed_df
    
    else:
        if st.session_state.df is None:
            st.info("👋 Welcome! Please upload a CSV file to get started.")
        else:
            st.success(f"✅ Data loaded: {len(st.session_state.df)} rows × {len(st.session_state.df.columns)} columns")
            st.info("📋 Use the sidebar to navigate between different features.")

if __name__ == "__main__":
    main()